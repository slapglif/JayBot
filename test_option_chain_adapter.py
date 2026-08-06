from decimal import Decimal

import pytest

from option_chain_adapter import (
    AlpacaOptionsAdapter,
    CboeDelayedOptionChainAdapter,
    DatabentoOpraAdapter,
    NasdaqCurrentOptionChainAdapter,
    chain_summary,
    parse_osi_symbol,
)


def test_parse_osi_symbol():
    contract = parse_osi_symbol("AAPL260807C00110000")
    assert contract.underlying == "AAPL"
    assert contract.expiration == "2026-08-07"
    assert contract.right == "C"
    assert contract.strike == Decimal("110")


def test_nasdaq_current_fetches_real_public_snapshot():
    try:
        chain = NasdaqCurrentOptionChainAdapter(timeout=30).fetch_chain("AAPL")
    except Exception as exc:  # pragma: no cover - public endpoint can rate-limit/reset CI
        pytest.skip(f"Nasdaq public endpoint unavailable: {exc}")
    summary = chain_summary(chain)
    assert summary["count"] >= 10
    assert summary["calls"] > 0
    assert summary["puts"] > 0
    assert chain[0].source == "nasdaq_current"
    assert chain[0].is_delayed is True
    assert chain[0].contract.underlying == "AAPL"


def test_cboe_delayed_fetches_real_public_snapshot():
    chain = CboeDelayedOptionChainAdapter(timeout=30).fetch_chain("AAPL")
    summary = chain_summary(chain)
    assert summary["count"] > 100
    assert summary["calls"] > 0
    assert summary["puts"] > 0
    assert chain[0].source == "cboe_delayed"
    assert chain[0].is_delayed is True
    assert chain[0].contract.underlying == "AAPL"


def test_cboe_rejects_historical_as_of():
    with pytest.raises(ValueError, match="historical"):
        CboeDelayedOptionChainAdapter().fetch_chain("AAPL", as_of="2024-01-02T15:30:00Z")


def test_authenticated_adapters_do_not_embed_credentials(monkeypatch):
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_KEY_ID", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="DATABENTO_API_KEY"):
        DatabentoOpraAdapter()
    with pytest.raises(RuntimeError, match="ALPACA_API_KEY_ID"):
        AlpacaOptionsAdapter()
