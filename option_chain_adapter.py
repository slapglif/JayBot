"""Provider-neutral option chain data adapters.

The goal of this module is to separate JayBot option-chain replay code from any
single vendor.  Adapters must not embed credentials.  Authenticated providers
should read keys from environment variables supplied by the caller.

Currently implemented:
- NasdaqCurrentOptionChainAdapter: public, no-auth, current option-chain table
  JSON from nasdaq.com.  This is useful for schema/prototype validation, not
  historical NBBO replay.
- CboeDelayedOptionChainAdapter: public, no-auth, current delayed option-chain
  snapshot from cboe.com/CDN.  Cboe's quote-table page prohibits automated
  downloading, so this adapter is retained for compatibility/research notes but
  should not be used for bulk automated collection without permission.

Documented placeholders:
- Databento OPRA.PILLAR: suitable for historical NBBO/trades/definitions, but
  requires a Databento account, API key, and licensed OPRA data purchase/credit.
- Alpaca options market data: indicative/free or OPRA with subscription; requires
  account API credentials and agreements.  Indicative data is not actual OPRA.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from decimal import Decimal
import json
import os
import re
import urllib.request
from typing import Any, Iterable, Literal, Protocol

import requests

OptionRight = Literal["C", "P"]
QuoteSource = Literal["nasdaq_current", "cboe_delayed", "databento_opra", "alpaca_indicative", "alpaca_opra"]

_OSI_RE = re.compile(r"^(?P<root>[A-Z0-9.\- ]{1,6})(?P<yy>\d{2})(?P<mm>\d{2})(?P<dd>\d{2})(?P<right>[CP])(?P<strike>\d{8})$")


@dataclass(frozen=True)
class OptionContract:
    """Point-in-time option contract identity in normalized OSI terms."""

    underlying: str
    option_symbol: str
    expiration: str  # YYYY-MM-DD
    right: OptionRight
    strike: Decimal


@dataclass(frozen=True)
class OptionQuote:
    """Provider-neutral option quote/chain row.

    Fields intentionally keep bid/ask/last/greeks nullable because public current
    chains and historical vendors differ in coverage.  Prices are per option
    share, not multiplied by 100.
    """

    contract: OptionContract
    quote_time: str | None
    source: QuoteSource
    is_delayed: bool
    bid: Decimal | None = None
    ask: Decimal | None = None
    bid_size: Decimal | None = None
    ask_size: Decimal | None = None
    last: Decimal | None = None
    last_trade_time: str | None = None
    volume: Decimal | None = None
    open_interest: Decimal | None = None
    implied_volatility: Decimal | None = None
    delta: Decimal | None = None
    gamma: Decimal | None = None
    theta: Decimal | None = None
    vega: Decimal | None = None
    rho: Decimal | None = None
    provider_payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, Decimal):
                return str(value)
            if hasattr(value, "__dataclass_fields__"):
                return {k: convert(v) for k, v in asdict(value).items()}
            if isinstance(value, dict):
                return {k: convert(v) for k, v in value.items()}
            return value

        return convert(self)


class OptionChainAdapter(Protocol):
    """Adapter protocol for current or historical option chain providers."""

    source: QuoteSource

    def fetch_chain(self, underlying: str, *, as_of: str | None = None) -> list[OptionQuote]:
        """Return a normalized chain snapshot.

        `as_of` is provider-specific.  Public Cboe supports only current delayed
        snapshots and raises if `as_of` is supplied.
        """


def _decimal_or_none(value: Any) -> Decimal | None:
    if value in (None, "", "null"):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def parse_osi_symbol(option_symbol: str, underlying_hint: str | None = None) -> OptionContract:
    """Parse an OSI/OCC option symbol such as AAPL260807C00110000."""

    match = _OSI_RE.match(option_symbol.strip())
    if not match:
        raise ValueError(f"Cannot parse OSI option symbol: {option_symbol!r}")
    parts = match.groupdict()
    year = 2000 + int(parts["yy"])
    expiration = f"{year:04d}-{int(parts['mm']):02d}-{int(parts['dd']):02d}"
    strike = Decimal(parts["strike"]) / Decimal(1000)
    root = parts["root"].strip()
    return OptionContract(
        underlying=(underlying_hint or root).upper(),
        option_symbol=option_symbol,
        expiration=expiration,
        right=parts["right"],  # type: ignore[arg-type]
        strike=strike,
    )


class NasdaqCurrentOptionChainAdapter:
    """No-auth adapter for Nasdaq's public current option-chain JSON table.

    Endpoint observed working 2026-08-06:
    https://api.nasdaq.com/api/quote/{SYMBOL}/option-chain?assetclass=stocks&limit=10000

    This endpoint exposes a current table only. It is not OPRA NBBO history and
    should be used only in ways permitted by Nasdaq's site/API terms.
    """

    source: QuoteSource = "nasdaq_current"
    base_url = "https://api.nasdaq.com/api/quote/{symbol}/option-chain?assetclass=stocks&limit=10"

    def __init__(self, session: requests.Session | None = None, timeout: int = 30) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_chain(self, underlying: str, *, as_of: str | None = None) -> list[OptionQuote]:
        if as_of is not None:
            raise ValueError("Nasdaq public option-chain endpoint is current snapshot only; historical as_of is unsupported")
        symbol = underlying.upper().replace(".", "-")
        url = self.base_url.format(symbol=symbol)
        headers = {
            "User-Agent": "Mozilla/5.0 JayBot option-chain research prototype",
            "Accept": "application/json",
            "Origin": "https://www.nasdaq.com",
            "Referer": "https://www.nasdaq.com/",
        }
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        data = payload.get("data", {})
        rows = data.get("table", {}).get("rows", [])
        last_trade = data.get("lastTrade") or ""
        year_match = re.search(r"\b(20\d{2})\b", last_trade)
        default_year = int(year_match.group(1)) if year_match else datetime.now(timezone.utc).year
        quotes: list[OptionQuote] = []
        current_year = default_year
        current_month_name: str | None = None
        for row in rows:
            expiry_group = row.get("expirygroup")
            if expiry_group:
                # Example: "August 7, 2026"
                try:
                    parsed = datetime.strptime(expiry_group, "%B %d, %Y")
                    current_year = parsed.year
                    current_month_name = parsed.strftime("%b")
                except ValueError:
                    pass
                continue
            expiry = row.get("expiryDate")
            strike = _decimal_or_none(row.get("strike"))
            if not expiry or strike is None:
                continue
            month_day = f"{expiry} {current_year}"
            try:
                expiry_date = datetime.strptime(month_day, "%b %d %Y").date().isoformat()
            except ValueError:
                continue
            strike_osi = int(strike * Decimal(1000))
            yy = str(current_year % 100).zfill(2)
            mmdd = datetime.strptime(month_day, "%b %d %Y").strftime("%m%d")
            root = underlying.upper()
            for right, prefix in (("C", "c"), ("P", "p")):
                option_symbol = f"{root}{yy}{mmdd}{right}{strike_osi:08d}"
                contract = OptionContract(root, option_symbol, expiry_date, right, strike)  # type: ignore[arg-type]
                quotes.append(
                    OptionQuote(
                        contract=contract,
                        quote_time=None,
                        source=self.source,
                        is_delayed=True,
                        bid=_decimal_or_none(row.get(f"{prefix}_Bid")),
                        ask=_decimal_or_none(row.get(f"{prefix}_Ask")),
                        last=_decimal_or_none(row.get(f"{prefix}_Last")),
                        volume=_decimal_or_none(row.get(f"{prefix}_Volume")),
                        open_interest=_decimal_or_none(row.get(f"{prefix}_Openinterest")),
                        provider_payload=row,
                    )
                )
        return quotes


class CboeDelayedOptionChainAdapter:
    """No-auth adapter for Cboe's public delayed quote-table JSON.

    Endpoint observed working 2026-08-06:
    https://cdn.cboe.com/api/global/delayed_quotes/options/{SYMBOL}.json

    Terms/licensing: use only as a delayed current snapshot prototype unless the
    Cboe site terms and data policies authorize the intended use.  It does not
    provide historical NBBO needed for JayBot backtest validation.
    """

    source: QuoteSource = "cboe_delayed"
    base_url = "https://cdn.cboe.com/api/global/delayed_quotes/options/{symbol}.json"

    def __init__(self, session: requests.Session | None = None, timeout: int = 30) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_chain(self, underlying: str, *, as_of: str | None = None) -> list[OptionQuote]:
        if as_of is not None:
            raise ValueError("Cboe public delayed endpoint is current snapshot only; historical as_of is unsupported")
        symbol = underlying.upper().replace(".", "_")
        url = self.base_url.format(symbol=symbol)
        response = self.session.get(url, timeout=self.timeout, headers={"User-Agent": "JayBot option-chain research prototype"})
        response.raise_for_status()
        payload = response.json()
        timestamp = payload.get("timestamp")
        rows = payload.get("data", {}).get("options", [])
        quotes: list[OptionQuote] = []
        for row in rows:
            option_symbol = row.get("option")
            if not option_symbol:
                continue
            contract = parse_osi_symbol(option_symbol, underlying_hint=underlying)
            quotes.append(
                OptionQuote(
                    contract=contract,
                    quote_time=timestamp,
                    source=self.source,
                    is_delayed=True,
                    bid=_decimal_or_none(row.get("bid")),
                    ask=_decimal_or_none(row.get("ask")),
                    bid_size=_decimal_or_none(row.get("bid_size")),
                    ask_size=_decimal_or_none(row.get("ask_size")),
                    last=_decimal_or_none(row.get("last_trade_price")),
                    last_trade_time=row.get("last_trade_time"),
                    volume=_decimal_or_none(row.get("volume")),
                    open_interest=_decimal_or_none(row.get("open_interest")),
                    implied_volatility=_decimal_or_none(row.get("iv")),
                    delta=_decimal_or_none(row.get("delta")),
                    gamma=_decimal_or_none(row.get("gamma")),
                    theta=_decimal_or_none(row.get("theta")),
                    vega=_decimal_or_none(row.get("vega")),
                    rho=_decimal_or_none(row.get("rho")),
                    provider_payload=row,
                )
            )
        return quotes


class DatabentoOpraAdapter:
    """Historical OPRA adapter skeleton; intentionally requires external key.

    To activate, install `databento`, set DATABENTO_API_KEY, have access to the
    OPRA.PILLAR dataset, and implement contract definition + quote replay calls.
    """

    source: QuoteSource = "databento_opra"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("DATABENTO_API_KEY")
        if not self.api_key:
            raise RuntimeError("DATABENTO_API_KEY is required; no credentials are embedded by JayBot")

    def fetch_chain(self, underlying: str, *, as_of: str | None = None) -> list[OptionQuote]:
        raise NotImplementedError(
            "Databento historical OPRA requires licensed OPRA.PILLAR access. "
            "Use instrument definitions to map listed contracts, then fetch NBBO/quotes/trades for the signal time."
        )


class AlpacaOptionsAdapter:
    """Alpaca options adapter skeleton; intentionally requires external keys.

    Free/Basic may expose indicative or delayed data depending on account and
    agreements.  Actual OPRA requires signed agreements/subscription. Indicative
    data must not be used as real historical NBBO evidence.
    """

    source: QuoteSource

    def __init__(self, *, source: QuoteSource = "alpaca_indicative", key_id: str | None = None, secret_key: str | None = None) -> None:
        if source not in ("alpaca_indicative", "alpaca_opra"):
            raise ValueError("Alpaca source must be alpaca_indicative or alpaca_opra")
        self.source = source
        self.key_id = key_id or os.environ.get("ALPACA_API_KEY_ID")
        self.secret_key = secret_key or os.environ.get("ALPACA_API_SECRET_KEY")
        if not (self.key_id and self.secret_key):
            raise RuntimeError("ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY are required; no credentials are embedded by JayBot")

    def fetch_chain(self, underlying: str, *, as_of: str | None = None) -> list[OptionQuote]:
        raise NotImplementedError("Alpaca implementation requires account credentials and source-specific entitlement checks")


def chain_summary(quotes: Iterable[OptionQuote]) -> dict[str, Any]:
    quotes = list(quotes)
    expirations = sorted({q.contract.expiration for q in quotes})
    calls = sum(1 for q in quotes if q.contract.right == "C")
    puts = sum(1 for q in quotes if q.contract.right == "P")
    return {
        "count": len(quotes),
        "calls": calls,
        "puts": puts,
        "first_expiration": expirations[0] if expirations else None,
        "last_expiration": expirations[-1] if expirations else None,
        "sample": quotes[0].to_dict() if quotes else None,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch a no-auth current option chain snapshot")
    parser.add_argument("symbol", nargs="?", default="AAPL")
    parser.add_argument("--provider", choices=["nasdaq", "cboe"], default="nasdaq")
    parser.add_argument("--json", action="store_true", help="Print full normalized rows as JSON")
    args = parser.parse_args()

    adapter = NasdaqCurrentOptionChainAdapter() if args.provider == "nasdaq" else CboeDelayedOptionChainAdapter()
    chain = adapter.fetch_chain(args.symbol)
    if args.json:
        print(json.dumps([q.to_dict() for q in chain], indent=2))
    else:
        print(json.dumps(chain_summary(chain), indent=2))
