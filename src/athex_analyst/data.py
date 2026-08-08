"""Market data access via Yahoo Finance (yfinance).

Data is delayed (typically ~15-20 minutes for European exchanges on Yahoo),
not tick-by-tick real-time. Suitable for a pre-market briefing and periodic
on-demand checks during the session, not for algorithmic execution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd
import yfinance as yf

from .tickers import Stock

logger = logging.getLogger(__name__)


@dataclass
class StockData:
    stock: Stock
    history: pd.DataFrame  # OHLCV, daily
    info: dict
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and not self.history.empty


def fetch_stock_data(stock: Stock, period: str = "1y") -> StockData:
    try:
        ticker = yf.Ticker(stock.symbol)
        history = ticker.history(period=period, auto_adjust=True)
        if history.empty:
            return StockData(stock, history, {}, error="Κενά ιστορικά δεδομένα")
        try:
            info = ticker.get_info()
        except Exception as exc:  # fundamentals are best-effort
            logger.warning("Fundamentals unavailable for %s: %s", stock.symbol, exc)
            info = {}
        return StockData(stock, history, info)
    except Exception as exc:
        logger.error("Failed to fetch %s: %s", stock.symbol, exc)
        return StockData(stock, pd.DataFrame(), {}, error=str(exc))


def fetch_universe(stocks: list[Stock], period: str = "1y") -> list[StockData]:
    results = []
    for stock in stocks:
        results.append(fetch_stock_data(stock, period=period))
    return results
