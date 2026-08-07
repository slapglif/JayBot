#!/usr/bin/env python
"""Two-year hourly validation of best discovered strategy — CORRECTED."""
import requests, json
from pathlib import Path
from dataclasses import dataclass
import pandas as pd
import numpy as np

START = '2024-08-07'
END = '2026-08-06'

# Canonical universe from config/winning_parameters.json
PAIRS = {
    'METU': 'META', 'AAPU': 'AAPL', 'MSFU': 'MSFT', 'NFXL': 'NFLX',
    'PLTU': 'PLTR', 'IBX': 'IBM', 'NVDU': 'NVDA', 'GGLL': 'GOOGL',
    'AMZU': 'AMZN', 'TSLT': 'TSLA'
}

CACHE = Path('data_cache')
UA = {'User-Agent': 'Mozilla/5.0'}

def fetch(t: str) -> pd.DataFrame:
    p = CACHE / f'{t}_{START}_{END}_1h.csv'
    if p.exists():
        d = pd.read_csv(p, index_col=0, parse_dates=True)
        # Columns might be out of order; standardize names
        d.columns = [c.strip().capitalize() for c in d.columns]
        d = d[['Open', 'High', 'Low', 'Close', 'Volume']]
        d.index = pd.to_datetime(d.index, utc=True).tz_convert('US/Eastern')
        return d
    p1 = int(pd.Timestamp(START, tz='UTC').timestamp())
    p2 = int(pd.Timestamp(END, tz='UTC').timestamp())
    u = f'https://query1.finance.yahoo.com/v8/finance/chart/{t}'
    r = requests.get(u, params={'period1': p1, 'period2': p2, 'interval': '1h', 'events': 'div,splits'},
                     headers=UA, timeout=60).json()['chart']['result']
    if not r:
        return pd.DataFrame()
    j = r[0]
    q = j['indicators']['quote'][0]
    d = pd.DataFrame(q, index=pd.to_datetime(j['timestamp'], unit='s', utc=True).tz_convert('US/Eastern')) \
        .rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}) \
        .dropna(subset=['Open', 'High', 'Low', 'Close'])
    d = d.between_time('09:30', '15:59')
    d.to_csv(p)
    return d

def load_inception_dates() -> dict[str, str]:
    """Load ETF inception dates from census CSV."""
    census = Path('data/etf_universe_census.csv')
    if not census.exists():
        return {}
    df = pd.read_csv(census)
    return dict(zip(df['symbol'], df['first_observed_price_date']))

def stitch(etf: str, under: str, etf_start: str | None) -> pd.DataFrame:
    """Build continuous index with clean splice at ETF inception — no cross-source leak."""
    e = fetch(etf)
    u = fetch(under)

    # Ensure we have data
    if len(u) == 0:
        return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'session', 'day_open'])

    # Split-adjusted levels from each source independently
    def level_from(source: pd.DataFrame) -> pd.DataFrame:
        if len(source) == 0:
            return pd.DataFrame(columns=['Level_Open', 'Level_High', 'Level_Low', 'Level_Close'])
        out = source.copy()
        out['Level_Open'] = 100.0 * out['Open'] / out['Open'].iloc[0]
        out['Level_High'] = 100.0 * out['High'] / out['Open'].iloc[0]
        out['Level_Low'] = 100.0 * out['Low'] / out['Open'].iloc[0]
        out['Level_Close'] = 100.0 * out['Close'] / out['Open'].iloc[0]
        return out

    e_lev = level_from(e)
    u_lev = level_from(u)

    # Transition date
    first = pd.Timestamp(etf_start, tz='US/Eastern') if etf_start else None

    # Splice: use underlying before ETF inception, ETF after
    if first is None:
        return u_lev[['Level_Open', 'Level_High', 'Level_Low', 'Level_Close']].rename(
            columns={'Level_Open': 'Open', 'Level_High': 'High', 'Level_Low': 'Low', 'Level_Close': 'Close'}
        )

    pre = u_lev[u_lev.index < first]
    post = e_lev[e_lev.index >= first]

    # Rescale post to match pre at the transition (clean splice)
    if len(pre) and len(post):
        pre_last = pre['Level_Close'].iloc[-1]
        post_first = post['Level_Open'].iloc[0]
        ratio = pre_last / post_first
        post = post * ratio

    combined = pd.concat([pre, post])[['Level_Open', 'Level_High', 'Level_Low', 'Level_Close']]
    combined = combined.rename(columns={'Level_Open': 'Open', 'Level_High': 'High', 'Level_Low': 'Low', 'Level_Close': 'Close'})
    combined['session'] = combined.index.date.astype(str)
    combined['day_open'] = combined.groupby('session').Open.transform('first')
    return combined

@dataclass
class Position:
    qty: float = 0.0
    cost: float = 0.0
    entries: int = 0
    last_session: int = -999
    opened: str = ''

def run(data: dict[str, pd.DataFrame], tp=50, wait=1, slip=5):
    # Decision times: 13:30 ET only if bar exists
    all_bars = {s: d for s, d in data.items() if len(d)}
    if not all_bars:
        return {}, pd.DataFrame(), pd.DataFrame(), {}

    decisions = sorted(set().union(*(
        set(d[(d.index.hour == 13) & (d.index.minute == 30)].index) for d in all_bars.values()
    )))

    sessions = sorted({x.date().isoformat() for x in decisions})
    if not sessions:
        return {}, pd.DataFrame(), pd.DataFrame(), {}

    sid = {s: i for i, s in enumerate(sessions)}
    cash = 100000.0
    pos = {}
    trades = []
    curve = []
    prev = None

    for dt in decisions:
        sn = sid[dt.date().isoformat()]

        # Exit check
        for s, p in list(pos.items()):
            if s not in data or len(data[s]) == 0:
                continue
            bars = data[s][(data[s].index <= dt) & ((data[s].index > prev) if prev is not None else True)]
            if len(bars) == 0:
                continue
            target = p.cost / p.qty * (1 + tp / 100)
            if bars.High.max() >= target:
                fill = target * (1 - slip / 10000)
                proceeds = p.qty * fill
                cash += proceeds
                trades.append([dt, s, 'EXIT', p.qty, fill, proceeds - p.cost, p.entries])
                del pos[s]

        # Mark-to-market equity
        equity = cash + sum(
            p.qty * float(data[s][data[s].index <= dt].iloc[-1].Close)
            for s, p in pos.items() if s in data and len(data[s][data[s].index <= dt])
        )

        # Eligible: declined from session open
        eligible = []
        for s, d in data.items():
            if dt in d.index:
                r = d.loc[dt]
                if r.Close < r.day_open:
                    eligible.append((float(r.Close / r.day_open - 1), s, float(r.Close)))

        bought = 0
        for drop, s, px in sorted(eligible):
            if bought >= 2:
                break
            p = pos.get(s)
            if p is not None and (p.entries >= 4 or sn - p.last_session < wait):
                continue

            order = equity * 0.025
            current_value = p.qty * px if p else 0.0
            if current_value + order > equity * 0.10 + 1e-8:
                continue

            fill = px * (1 + slip / 10000)
            qty = order / fill
            if order > cash:
                continue

            cash -= order
            if p is None:
                p = Position(opened=str(dt))
                pos[s] = p
            p.qty += qty
            p.cost += order
            p.entries += 1
            p.last_session = sn
            trades.append([dt, s, 'BUY', qty, fill, 0.0, p.entries])
            bought += 1

        equity = cash + sum(
            p.qty * float(data[s][data[s].index <= dt].iloc[-1].Close)
            for s, p in pos.items() if s in data and len(data[s][data[s].index <= dt])
        )
        curve.append([dt, equity, cash, len(pos)])
        prev = dt

    eq = pd.DataFrame(curve, columns=['timestamp', 'equity', 'cash', 'positions']).set_index('timestamp')
    td = pd.DataFrame(trades, columns=['timestamp', 'symbol', 'side', 'qty', 'price', 'pnl', 'entries'])
    final = float(eq.iloc[-1].equity)
    dd = float((eq.equity / eq.equity.cummax() - 1).min())
    years = len(sessions) / 252

    stats = {
        'start': sessions[0], 'end': sessions[-1], 'sessions': len(sessions),
        'final': final, 'return_pct': (final / 100000 - 1) * 100,
        'cagr_pct': ((final / 100000) ** (1 / years) - 1) * 100,
        'max_dd_pct': dd * 100, 'orders': len(td),
        'buys': int((td.side == 'BUY').sum()), 'exits': int((td.side == 'EXIT').sum()),
        'open': len(pos), 'tp': tp, 'wait': wait,
        'purchases_per_day': 2, 'entry_pct': 2.5, 'max_asset_pct': 10
    }
    return stats, td, eq, pos

def main():
    inceptions = load_inception_dates()
    data = {}
    inc = {}
    for e, u in PAIRS.items():
        etf_start = inceptions.get(e)
        data[e] = stitch(e, u, etf_start)
        inc[e] = etf_start

    s, t, e, p = run(data)

    out = Path('backtest_results/kitty_2_5pct_tp50_2y_hourly')
    out.mkdir(parents=True, exist_ok=True)

    t.assign(order_date_et=pd.to_datetime(t.timestamp, utc=True).dt.tz_convert('US/Eastern').dt.strftime('%Y-%m-%d')) \
        .to_csv(out / 'orders_with_dates.csv', index=False)
    e.to_csv(out / 'equity_curve.csv')

    # Symbol attribution
    if len(t):
        exits = t[t.side == 'EXIT']
        if len(exits):
            attribution = exits.groupby('symbol')['pnl'].sum().to_dict()
        else:
            attribution = {sym: 0.0 for sym in PAIRS}
        # Add open position PnL
        for sym, pos_obj in p.items():
            if sym in data and len(data[sym]):
                last = data[sym].iloc[-1].Close
                attr = pos_obj.qty * last - pos_obj.cost
                attribution[sym] = attribution.get(sym, 0.0) + attr
        pd.DataFrame([{'symbol': k, 'pnl': v} for k, v in attribution.items()]) \
            .to_csv(out / 'symbol_attribution.csv', index=False)

    (out / 'summary.json').write_text(json.dumps({'stats': s, 'inceptions': inc}, indent=2))
    print(json.dumps(s, indent=2))
    print('inceptions', inc)

if __name__ == '__main__':
    main()
