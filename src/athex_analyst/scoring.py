"""Rule-based scoring engine that turns technical + fundamental signals into
a recommendation. This is a transparent, explainable heuristic model — not a
predictive/ML model, and not investment advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .data import StockData
from .indicators import TechnicalSnapshot


@dataclass
class SignalContribution:
    label: str
    points: float
    note: str


@dataclass
class Recommendation:
    stock_data: StockData
    score: float
    verdict: str
    signals: list[SignalContribution] = field(default_factory=list)
    snapshot: TechnicalSnapshot | None = None

    @property
    def symbol(self) -> str:
        return self.stock_data.stock.symbol

    @property
    def name(self) -> str:
        return self.stock_data.stock.name_el


VERDICT_STRONG_BUY = "ΙΣΧΥΡΗ ΑΓΟΡΑ"
VERDICT_BUY = "ΑΓΟΡΑ"
VERDICT_HOLD = "ΟΥΔΕΤΕΡΟ / ΚΡΑΤΗΣΗ"
VERDICT_AVOID = "ΑΠΟΦΥΓΗ"


def _verdict_for_score(score: float) -> str:
    if score >= 50:
        return VERDICT_STRONG_BUY
    if score >= 20:
        return VERDICT_BUY
    if score >= -20:
        return VERDICT_HOLD
    return VERDICT_AVOID


def score_stock(sd: StockData) -> Recommendation | None:
    if not sd.ok:
        return None

    snap = TechnicalSnapshot(sd.history)
    signals: list[SignalContribution] = []
    total = 0.0

    # --- Trend: price vs SMA50 / SMA200, golden/death cross ---
    if snap.sma50 is not None and snap.sma200 is not None:
        if snap.last_close > snap.sma50 > snap.sma200:
            pts = 15
            signals.append(SignalContribution("Ανοδική τάση", pts, "Τιμή > SMA50 > SMA200 (golden setup)"))
            total += pts
        elif snap.last_close < snap.sma50 < snap.sma200:
            pts = -15
            signals.append(SignalContribution("Πτωτική τάση", pts, "Τιμή < SMA50 < SMA200 (death setup)"))
            total += pts
        elif snap.last_close > snap.sma200:
            pts = 5
            signals.append(SignalContribution("Μακροπρόθεσμη τάση", pts, "Τιμή πάνω από SMA200"))
            total += pts
        else:
            pts = -5
            signals.append(SignalContribution("Μακροπρόθεσμη τάση", pts, "Τιμή κάτω από SMA200"))
            total += pts

    # --- Momentum: RSI ---
    if snap.rsi14 is not None:
        if snap.rsi14 < 30:
            pts = 12
            signals.append(SignalContribution("RSI", pts, f"Υπερπουλημένη ζώνη (RSI={snap.rsi14:.1f})"))
            total += pts
        elif snap.rsi14 > 70:
            pts = -12
            signals.append(SignalContribution("RSI", pts, f"Υπεραγορασμένη ζώνη (RSI={snap.rsi14:.1f})"))
            total += pts
        elif 45 <= snap.rsi14 <= 60:
            pts = 5
            signals.append(SignalContribution("RSI", pts, f"Ουδέτερο-θετικό momentum (RSI={snap.rsi14:.1f})"))
            total += pts

    # --- MACD crossover ---
    if snap.macd is not None and snap.macd_signal is not None:
        bullish_cross = (
            snap.macd_hist is not None
            and snap.macd_hist_prev is not None
            and snap.macd_hist > 0
            and snap.macd_hist_prev <= 0
        )
        bearish_cross = (
            snap.macd_hist is not None
            and snap.macd_hist_prev is not None
            and snap.macd_hist < 0
            and snap.macd_hist_prev >= 0
        )
        if bullish_cross:
            pts = 15
            signals.append(SignalContribution("MACD", pts, "Πρόσφατη ανοδική διασταύρωση (bullish crossover)"))
            total += pts
        elif bearish_cross:
            pts = -15
            signals.append(SignalContribution("MACD", pts, "Πρόσφατη πτωτική διασταύρωση (bearish crossover)"))
            total += pts
        elif snap.macd > snap.macd_signal:
            pts = 5
            signals.append(SignalContribution("MACD", pts, "MACD πάνω από τη γραμμή σήματος"))
            total += pts
        else:
            pts = -5
            signals.append(SignalContribution("MACD", pts, "MACD κάτω από τη γραμμή σήματος"))
            total += pts

    # --- Bollinger Bands: mean-reversion signal ---
    if snap.bb_lower is not None and snap.bb_upper is not None:
        if snap.last_close <= snap.bb_lower:
            pts = 8
            signals.append(SignalContribution("Bollinger Bands", pts, "Τιμή στο/κάτω από το κάτω άκρο (πιθανή αναπήδηση)"))
            total += pts
        elif snap.last_close >= snap.bb_upper:
            pts = -8
            signals.append(SignalContribution("Bollinger Bands", pts, "Τιμή στο/πάνω από το άνω άκρο (πιθανή διόρθωση)"))
            total += pts

    # --- Volume confirmation ---
    if snap.avg_volume20 and snap.avg_volume20 > 0:
        vol_ratio = snap.volume / snap.avg_volume20
        if vol_ratio > 1.5 and snap.change_pct > 0:
            pts = 8
            signals.append(SignalContribution("Όγκος", pts, f"Αυξημένος όγκος ({vol_ratio:.1f}x μ.ο.) με ανοδική κίνηση"))
            total += pts
        elif vol_ratio > 1.5 and snap.change_pct < 0:
            pts = -8
            signals.append(SignalContribution("Όγκος", pts, f"Αυξημένος όγκος ({vol_ratio:.1f}x μ.ο.) με πτωτική κίνηση"))
            total += pts

    # --- Distance from 52-week range ---
    if snap.week52_high > snap.week52_low:
        pos = (snap.last_close - snap.week52_low) / (snap.week52_high - snap.week52_low)
        if pos < 0.2:
            pts = 6
            signals.append(SignalContribution("52-εβδ. εύρος", pts, f"Κοντά στο χαμηλό 52 εβδομάδων ({pos*100:.0f}% του εύρους)"))
            total += pts
        elif pos > 0.9:
            pts = -4
            signals.append(SignalContribution("52-εβδ. εύρος", pts, f"Κοντά στο υψηλό 52 εβδομάδων ({pos*100:.0f}% του εύρους)"))
            total += pts

    # --- Basic fundamentals (best-effort; Yahoo data for ATHEX names is often sparse) ---
    info = sd.info or {}
    trailing_pe = info.get("trailingPE")
    if isinstance(trailing_pe, (int, float)) and trailing_pe > 0:
        if trailing_pe < 10:
            pts = 8
            signals.append(SignalContribution("P/E", pts, f"Χαμηλός δείκτης P/E ({trailing_pe:.1f})"))
            total += pts
        elif trailing_pe > 25:
            pts = -6
            signals.append(SignalContribution("P/E", pts, f"Υψηλός δείκτης P/E ({trailing_pe:.1f})"))
            total += pts

    dividend_yield = info.get("dividendYield")
    if isinstance(dividend_yield, (int, float)) and dividend_yield > 0:
        dy_pct = dividend_yield * 100 if dividend_yield < 1 else dividend_yield
        if dy_pct >= 5:
            pts = 6
            signals.append(SignalContribution("Μερισματική Απόδοση", pts, f"Υψηλή μερισματική απόδοση ({dy_pct:.1f}%)"))
            total += pts

    score = max(-100.0, min(100.0, total))
    verdict = _verdict_for_score(score)
    return Recommendation(stock_data=sd, score=score, verdict=verdict, signals=signals, snapshot=snap)


def rank_recommendations(stock_data_list: list[StockData]) -> list[Recommendation]:
    recs = [score_stock(sd) for sd in stock_data_list]
    valid = [r for r in recs if r is not None]
    valid.sort(key=lambda r: r.score, reverse=True)
    return valid
