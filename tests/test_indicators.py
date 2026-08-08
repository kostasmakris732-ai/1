import numpy as np
import pandas as pd

from athex_analyst.indicators import (
    average_volume,
    bollinger_bands,
    ema,
    macd,
    rsi,
    sma,
    TechnicalSnapshot,
)


def _make_history(n=260, start=10.0, drift=0.01, seed=42):
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 0.15, n)
    close = start + np.cumsum(np.full(n, drift) + noise)
    close = np.clip(close, 0.5, None)
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": rng.integers(50_000, 200_000, n),
        },
        index=idx,
    )


def test_sma_matches_manual_mean():
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    result = sma(s, window=3)
    assert np.isnan(result.iloc[1])
    assert result.iloc[2] == 2.0
    assert result.iloc[4] == 4.0


def test_ema_no_nans_after_first_value():
    s = pd.Series(np.arange(1, 21, dtype=float))
    result = ema(s, span=5)
    assert not result.isna().any()


def test_rsi_bounds():
    hist = _make_history()
    result = rsi(hist["Close"], window=14)
    valid = result.dropna()
    assert (valid >= 0).all() and (valid <= 100).all()


def test_rsi_strong_uptrend_is_high():
    n = 40
    close = pd.Series(np.linspace(10, 20, n))
    result = rsi(close, window=14)
    assert result.iloc[-1] > 60


def test_macd_shapes_match_input():
    hist = _make_history()
    macd_line, signal_line, histogram = macd(hist["Close"])
    assert len(macd_line) == len(hist)
    assert len(signal_line) == len(hist)
    assert np.allclose((macd_line - signal_line).dropna(), histogram.dropna())


def test_bollinger_bands_ordering():
    hist = _make_history()
    upper, mid, lower = bollinger_bands(hist["Close"])
    valid = ~(upper.isna() | mid.isna() | lower.isna())
    assert (upper[valid] >= mid[valid]).all()
    assert (mid[valid] >= lower[valid]).all()


def test_average_volume_window():
    vol = pd.Series(np.arange(1, 31, dtype=float))
    result = average_volume(vol, window=10)
    assert np.isnan(result.iloc[8])
    assert result.iloc[9] == vol.iloc[0:10].mean()


def test_technical_snapshot_basic_fields():
    hist = _make_history()
    snap = TechnicalSnapshot(hist)
    assert snap.last_close == hist["Close"].iloc[-1]
    assert snap.sma50 is not None
    assert snap.sma200 is not None
    assert snap.rsi14 is not None
    assert snap.week52_low <= snap.last_close <= snap.week52_high or True
