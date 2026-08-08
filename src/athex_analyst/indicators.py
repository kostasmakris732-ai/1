"""Technical indicators computed from OHLCV price history."""

from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    result = 100 - (100 / (1 + rs))
    result = result.where(avg_loss != 0, other=100.0)
    result = result.where(~((avg_loss == 0) & (avg_gain == 0)), other=50.0)
    return result.fillna(50)


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
    mid = sma(series, window)
    std = series.rolling(window=window, min_periods=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def average_volume(volume: pd.Series, window: int = 20) -> pd.Series:
    return volume.rolling(window=window, min_periods=window).mean()


class TechnicalSnapshot:
    """Latest-bar technical readout for a single stock."""

    def __init__(self, history: pd.DataFrame):
        close = history["Close"]
        self.last_close = float(close.iloc[-1])
        self.prev_close = float(close.iloc[-2]) if len(close) > 1 else self.last_close
        self.change_pct = (
            (self.last_close - self.prev_close) / self.prev_close * 100
            if self.prev_close
            else 0.0
        )

        self.sma50 = _last_valid(sma(close, 50))
        self.sma200 = _last_valid(sma(close, 200))
        self.rsi14 = _last_valid(rsi(close, 14))

        macd_line, signal_line, hist = macd(close)
        self.macd = _last_valid(macd_line)
        self.macd_signal = _last_valid(signal_line)
        self.macd_hist = _last_valid(hist)
        self.macd_hist_prev = _last_valid(hist, offset=2)

        upper, mid, lower = bollinger_bands(close)
        self.bb_upper = _last_valid(upper)
        self.bb_lower = _last_valid(lower)

        vol = history["Volume"]
        self.volume = float(vol.iloc[-1])
        self.avg_volume20 = _last_valid(average_volume(vol, 20))

        self.week52_high = float(close.tail(252).max())
        self.week52_low = float(close.tail(252).min())


def _last_valid(series: pd.Series, offset: int = 1) -> float | None:
    clean = series.dropna()
    if len(clean) < offset:
        return None
    return float(clean.iloc[-offset])
