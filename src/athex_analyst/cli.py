"""CLI entrypoint.

Usage:
    python -m athex_analyst.cli --report reports/premarket.md --dashboard reports/dashboard.html
    python -m athex_analyst.cli --title "Ενδοσυνεδριακή Ενημέρωση"
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .data import fetch_universe
from .dashboard import build_dashboard_html
from .report import DISCLAIMER_PLAIN_EL, build_console_summary, build_markdown_report
from .scoring import rank_recommendations
from .tickers import get_universe

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run(
    report_path: str | None,
    dashboard_path: str | None,
    title: str,
    top_n: int,
    period: str,
) -> int:
    universe = get_universe()
    logger.info("Fetching data for %d ATHEX tickers...", len(universe))
    stock_data = fetch_universe(universe, period=period)

    errors = [(sd.stock.symbol, sd.error) for sd in stock_data if not sd.ok]
    recommendations = rank_recommendations(stock_data)

    if not recommendations:
        logger.error("No usable data fetched for any ticker. Errors: %s", errors)
        print(build_console_summary([]))
        return 1

    print(build_console_summary(recommendations, top_n=top_n))

    if report_path:
        md = build_markdown_report(recommendations, title=title, top_n=top_n, errors=errors)
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        Path(report_path).write_text(md, encoding="utf-8")
        logger.info("Markdown report written to %s", report_path)

    if dashboard_path:
        htmldoc = build_dashboard_html(recommendations, disclaimer=DISCLAIMER_PLAIN_EL)
        Path(dashboard_path).parent.mkdir(parents=True, exist_ok=True)
        Path(dashboard_path).write_text(htmldoc, encoding="utf-8")
        logger.info("HTML dashboard written to %s", dashboard_path)

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ΧΑΑ Financial Analyst — buy-signal report generator")
    parser.add_argument("--report", dest="report_path", default="reports/premarket.md", help="Path to write the markdown report")
    parser.add_argument("--dashboard", dest="dashboard_path", default="reports/dashboard.html", help="Path to write the HTML dashboard")
    parser.add_argument("--title", default="Πρωινή Αναφορά ΧΑΑ", help="Report title")
    parser.add_argument("--top", dest="top_n", type=int, default=8, help="Number of top candidates to highlight")
    parser.add_argument("--period", default="1y", help="History window passed to yfinance (e.g. 6mo, 1y, 2y)")
    parser.add_argument("--no-report", action="store_true", help="Skip writing the markdown report")
    parser.add_argument("--no-dashboard", action="store_true", help="Skip writing the HTML dashboard")
    args = parser.parse_args(argv)

    return run(
        report_path=None if args.no_report else args.report_path,
        dashboard_path=None if args.no_dashboard else args.dashboard_path,
        title=args.title,
        top_n=args.top_n,
        period=args.period,
    )


if __name__ == "__main__":
    sys.exit(main())
