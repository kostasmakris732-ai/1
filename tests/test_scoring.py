import numpy as np
import pandas as pd

from athex_analyst.data import StockData
from athex_analyst.scoring import (
    VERDICT_AVOID,
    VERDICT_BUY,
    VERDICT_HOLD,
    VERDICT_STRONG_BUY,
    rank_recommendations,
    score_stock,
)
from athex_analyst.tickers import Stock


def _stock_data(close_values, symbol="TEST.AT", info=None):
    n = len(close_values)
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = pd.Series(close_values, index=idx)
    hist = pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": pd.Series(np.full(n, 100_000.0), index=idx),
        }
    )
    stock = Stock(symbol, "Δοκιμαστική", "Δοκιμή")
    return StockData(stock, hist, info or {})


def test_score_stock_returns_none_on_error():
    stock = Stock("BAD.AT", "Bad", "Sector")
    sd = StockData(stock, pd.DataFrame(), {}, error="no data")
    assert score_stock(sd) is None


def _noisy_trend(n, start, drift, seed):
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 0.2, n)
    close = start + np.cumsum(np.full(n, drift) + noise)
    return np.clip(close, 0.5, None)


def test_strong_uptrend_scores_positive():
    # Realistic uptrend with volatility (not monotonic), so it doesn't sit
    # pinned at RSI=100 / exactly at its 52-week high like a straight line would.
    close = _noisy_trend(260, start=10, drift=0.08, seed=7)
    sd = _stock_data(close)
    rec = score_stock(sd)
    assert rec is not None
    assert rec.score > 0
    assert rec.verdict != VERDICT_AVOID


def test_strong_downtrend_scores_negative():
    close = _noisy_trend(260, start=50, drift=-0.08, seed=7)
    sd = _stock_data(close)
    rec = score_stock(sd)
    assert rec is not None
    assert rec.score < 0
    assert rec.verdict != VERDICT_STRONG_BUY


def test_uptrend_scores_higher_than_downtrend():
    up = _noisy_trend(260, start=10, drift=0.08, seed=7)
    down = _noisy_trend(260, start=50, drift=-0.08, seed=7)
    rec_up = score_stock(_stock_data(up, symbol="UP.AT"))
    rec_down = score_stock(_stock_data(down, symbol="DOWN.AT"))
    assert rec_up.score > rec_down.score


def test_flat_series_is_neutral_ish():
    n = 260
    rng = np.random.default_rng(1)
    close = 20 + rng.normal(0, 0.01, n)
    sd = _stock_data(close)
    rec = score_stock(sd)
    assert rec is not None
    assert -30 <= rec.score <= 30


def test_rank_recommendations_sorted_descending():
    n = 260
    up = 10 + np.cumsum(np.full(n, 0.05))
    down = 50 - np.cumsum(np.full(n, 0.05))
    down = np.clip(down, 1, None)
    sd_up = _stock_data(up, symbol="UP.AT")
    sd_down = _stock_data(down, symbol="DOWN.AT")
    ranked = rank_recommendations([sd_down, sd_up])
    assert ranked[0].symbol == "UP.AT"
    assert ranked[0].score >= ranked[1].score


def test_low_pe_and_high_dividend_boost_score():
    n = 260
    rng = np.random.default_rng(2)
    close = 20 + rng.normal(0, 0.01, n)
    sd_plain = _stock_data(close, symbol="PLAIN.AT")
    sd_cheap = _stock_data(close, symbol="CHEAP.AT", info={"trailingPE": 6.0, "dividendYield": 0.07})
    rec_plain = score_stock(sd_plain)
    rec_cheap = score_stock(sd_cheap)
    assert rec_cheap.score > rec_plain.score
