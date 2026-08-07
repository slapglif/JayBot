import pandas as pd
from share_falsification_100 import Rule,simulate


def bars(mult=1.0):
    idx=pd.date_range("2020-01-02",periods=8,freq="B")
    return pd.DataFrame({"Open":[100*mult]*8,"High":[101*mult]*7+[160*mult],"Low":[89*mult]*8,"Close":[90*mult]*7+[150*mult],"Volume":[1_000_000]*8},index=idx)


def test_two_distinct_purchases_per_day_and_mark_to_market():
    data={f"S{i}":bars(1+i/10) for i in range(4)}
    stats,orders,equity,open_pnl=simulate(data,Rule(tp=5.0))
    first=orders[(orders.side=="BUY") & (orders.date==orders.date.min())]
    assert len(first)==2
    assert first.symbol.nunique()==2
    assert stats["orders"]==len(orders)
    assert abs(equity.iloc[-1].equity-(equity.iloc[-1].cash+equity.iloc[-1].exposure))<1e-8


def test_asset_cap_blocks_fifth_or_overweight_tranche():
    data={"ONLY":bars()}
    stats,orders,_,_=simulate(data,Rule(tp=5.0,entry_pct=.025,max_tranches=4))
    assert len(orders[orders.side=="BUY"])<=4


def test_target_exit_is_realized_and_reconciled():
    data={"ONLY":bars()}
    stats,orders,equity,open_pnl=simulate(data,Rule(tp=.50,purchases_per_day=1,max_tranches=1))
    exits=orders[orders.side=="EXIT"]
    assert len(exits)==1
    assert exits.iloc[0].pnl>0
    assert abs(stats["realized_pnl"]-exits.pnl.sum())<1e-8
    assert abs(equity.iloc[-1].equity-(100000+stats["realized_pnl"]+stats["open_pnl"]))<1e-6
