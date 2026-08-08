"""Human-readable (Greek) reports from a ranked recommendation list."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from .scoring import Recommendation, VERDICT_AVOID, VERDICT_BUY, VERDICT_HOLD, VERDICT_STRONG_BUY

ATHENS_TZ = ZoneInfo("Europe/Athens")

DISCLAIMER_EL = (
    "⚠️ **Αποποίηση ευθύνης**: Η αναφορά αυτή παράγεται αυτόματα από κανόνες τεχνικής "
    "ανάλυσης (SMA/RSI/MACD/Bollinger) και βασικών θεμελιωδών στοιχείων. Τα δεδομένα "
    "τιμών προέρχονται από το Yahoo Finance και έχουν καθυστέρηση (δεν είναι real-time "
    "tick-by-tick). ΔΕΝ αποτελεί επενδυτική συμβουλή, σύσταση αγοράς/πώλησης ούτε "
    "εξατομικευμένη επενδυτική υπηρεσία υπό την έννοια του ν.4514/2018 (MiFID II). Η "
    "επένδυση σε μετοχές ενέχει κίνδυνο απώλειας κεφαλαίου. Πριν από κάθε επενδυτική "
    "απόφαση συμβουλευτείτε αδειοδοτημένο επενδυτικό σύμβουλο."
)

DISCLAIMER_PLAIN_EL = (
    "Αποποίηση ευθύνης: Η αναφορά αυτή παράγεται αυτόματα από κανόνες τεχνικής "
    "ανάλυσης (SMA/RSI/MACD/Bollinger) και βασικών θεμελιωδών στοιχείων. Τα δεδομένα "
    "τιμών προέρχονται από το Yahoo Finance και έχουν καθυστέρηση (δεν είναι real-time "
    "tick-by-tick). ΔΕΝ αποτελεί επενδυτική συμβουλή, σύσταση αγοράς/πώλησης ούτε "
    "εξατομικευμένη επενδυτική υπηρεσία υπό την έννοια του ν.4514/2018 (MiFID II). Η "
    "επένδυση σε μετοχές ενέχει κίνδυνο απώλειας κεφαλαίου. Πριν από κάθε επενδυτική "
    "απόφαση συμβουλευτείτε αδειοδοτημένο επενδυτικό σύμβουλο."
)

VERDICT_EMOJI = {
    VERDICT_STRONG_BUY: "🟢",
    VERDICT_BUY: "🟢",
    VERDICT_HOLD: "🟡",
    VERDICT_AVOID: "🔴",
}


def _fmt_pct(x: float) -> str:
    sign = "+" if x >= 0 else ""
    return f"{sign}{x:.2f}%"


def build_markdown_report(
    recommendations: list[Recommendation],
    title: str = "Πρωινή Αναφορά ΧΑΑ",
    top_n: int = 8,
    errors: list[tuple[str, str]] | None = None,
) -> str:
    now = datetime.now(ATHENS_TZ)
    lines = [
        f"# {title}",
        "",
        f"_Παράχθηκε: {now.strftime('%A %d/%m/%Y %H:%M')} (ώρα Ελλάδας)_",
        "",
        DISCLAIMER_EL,
        "",
        "---",
        "",
        f"## 🏆 Top {top_n} υποψήφιες θέσεις αγοράς (FTSE/Athex Large Cap)",
        "",
        "| # | Μετοχή | Ticker | Τιμή | Μεταβολή | Σκορ | Σήμα |",
        "|---|--------|--------|------|----------|------|------|",
    ]

    buy_candidates = [r for r in recommendations if r.verdict in (VERDICT_STRONG_BUY, VERDICT_BUY)]
    top = buy_candidates[:top_n] if buy_candidates else recommendations[:top_n]

    for i, rec in enumerate(top, start=1):
        snap = rec.snapshot
        emoji = VERDICT_EMOJI.get(rec.verdict, "⚪")
        lines.append(
            f"| {i} | {rec.name} | `{rec.symbol}` | {snap.last_close:.2f}€ | "
            f"{_fmt_pct(snap.change_pct)} | {rec.score:+.0f} | {emoji} {rec.verdict} |"
        )

    lines += ["", "---", "", "## 📋 Ανάλυση ανά μετοχή", ""]

    for rec in recommendations:
        snap = rec.snapshot
        emoji = VERDICT_EMOJI.get(rec.verdict, "⚪")
        lines.append(f"### {emoji} {rec.name} (`{rec.symbol}`) — {rec.verdict}")
        header = f"Τιμή: **{snap.last_close:.2f}€** ({_fmt_pct(snap.change_pct)}) · Σκορ: **{rec.score:+.0f}/100**"
        if snap.rsi14 is not None:
            header += f" · RSI(14): {snap.rsi14:.1f}"
        lines.append(header)
        if rec.signals:
            for sig in rec.signals:
                sign = "+" if sig.points >= 0 else ""
                lines.append(f"- {sig.label}: {sign}{sig.points:.0f} — {sig.note}")
        else:
            lines.append("- Δεν εντοπίστηκαν ισχυρά σήματα.")
        lines.append("")

    if errors:
        lines += ["---", "", "## ⚠️ Μετοχές χωρίς δεδομένα", ""]
        for symbol, err in errors:
            lines.append(f"- `{symbol}`: {err}")
        lines.append("")

    lines += ["---", "", DISCLAIMER_EL]
    return "\n".join(lines)


def build_console_summary(recommendations: list[Recommendation], top_n: int = 8) -> str:
    lines = ["ΧΑΑ — Σύνοψη Προτάσεων", "=" * 40]
    buy_candidates = [r for r in recommendations if r.verdict in (VERDICT_STRONG_BUY, VERDICT_BUY)]
    top = buy_candidates[:top_n] if buy_candidates else recommendations[:top_n]
    for rec in top:
        emoji = VERDICT_EMOJI.get(rec.verdict, "⚪")
        lines.append(
            f"{emoji} {rec.symbol:<10} {rec.snapshot.last_close:>8.2f}€ "
            f"{_fmt_pct(rec.snapshot.change_pct):>8} score={rec.score:+.0f} {rec.verdict}"
        )
    lines.append("")
    lines.append("Δεν αποτελεί επενδυτική συμβουλή.")
    return "\n".join(lines)
