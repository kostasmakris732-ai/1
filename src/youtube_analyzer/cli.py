"""CLI entrypoint.

Usage:
    python -m youtube_analyzer.cli analyze <url_or_id> [--report PATH] [--no-library]
    python -m youtube_analyzer.cli subtitles <url_or_id> [--out PATH] [--lang el]
    python -m youtube_analyzer.cli compare <url_or_id> --start 12:34 --end 15:10 [--report PATH]
    python -m youtube_analyzer.cli tab <url_or_id> --start 2:25 --end 3:00 [--fps 1.0]
    python -m youtube_analyzer.cli lesson <url_or_id> --start 2:25 --end 3:00 [--max-related 5]
    python -m youtube_analyzer.cli library-list
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .library import DEFAULT_LIBRARY_DIR, list_video_ids, load_all, load_analysis, save_analysis
from .subtitles import segments_to_srt
from .timecode import parse_timecode
from .youtube_client import extract_video_id

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def cmd_analyze(args: argparse.Namespace) -> int:
    from .pipeline import analyze_video
    from .report import build_analysis_markdown

    analysis = analyze_video(
        args.url,
        asr_model=args.asr_model,
        translate_summary=not args.no_translate,
    )

    if not args.no_library:
        path = save_analysis(analysis, library_dir=args.library_dir)
        logger.info("Αποθηκεύτηκε στη βιβλιοθήκη: %s", path)

    md = build_analysis_markdown(analysis)
    report_path = args.report_path or f"reports/youtube/{analysis.metadata.video_id}.md"
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(md, encoding="utf-8")
    logger.info("Αναφορά ανάλυσης γράφτηκε στο %s", report_path)
    print(md)
    return 0


def cmd_subtitles(args: argparse.Namespace) -> int:
    from .pipeline import build_greek_subtitles

    video_id = extract_video_id(args.url)
    segments = build_greek_subtitles(args.url, asr_model=args.asr_model)
    srt = segments_to_srt(segments)

    out_path = args.out or f"reports/youtube/{video_id}.el.srt"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(srt, encoding="utf-8")
    logger.info("Ελληνικοί υπότιτλοι γράφτηκαν στο %s (%d cues)", out_path, srt.count(" --> "))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    from .chunking import build_chunks
    from .compare import compare_segment
    from .pipeline import get_transcript
    from .report import build_compare_markdown
    from .youtube_client import fetch_metadata
    from .models import VideoAnalysis

    video_id = extract_video_id(args.url)
    start = parse_timecode(args.start)
    end = parse_timecode(args.end)
    if end <= start:
        logger.error("Το --end πρέπει να είναι μετά το --start")
        return 1

    source = load_analysis(video_id, library_dir=args.library_dir)
    if source is None:
        logger.info("Το βίντεο δεν υπάρχει στη βιβλιοθήκη — γίνεται ανάλυση τώρα...")
        metadata = fetch_metadata(args.url)
        transcript = get_transcript(args.url, asr_model=args.asr_model)
        chunks = build_chunks(transcript)
        source = VideoAnalysis(metadata=metadata, transcript=transcript, chunks=chunks)
        save_analysis(source, library_dir=args.library_dir)

    corpus = load_all(library_dir=args.library_dir)
    matches = compare_segment(source, start, end, corpus, top_k=args.top, min_score=args.min_score)

    md = build_compare_markdown(source, start, end, matches)
    report_path = args.report_path or f"reports/youtube/{video_id}.compare.md"
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(md, encoding="utf-8")
    logger.info("Αναφορά σύγκρισης γράφτηκε στο %s", report_path)
    print(md)
    return 0


def cmd_tab(args: argparse.Namespace) -> int:
    from .library import load_analysis
    from .ocr_tab import extract_tab_ocr
    from .report import build_tab_markdown
    from .youtube_client import fetch_metadata
    from .models import Transcript, VideoAnalysis

    video_id = extract_video_id(args.url)
    start = parse_timecode(args.start)
    end = parse_timecode(args.end)
    if end <= start:
        logger.error("Το --end πρέπει να είναι μετά το --start")
        return 1

    source = load_analysis(video_id, library_dir=args.library_dir)
    if source is None:
        metadata = fetch_metadata(args.url)
        source = VideoAnalysis(metadata=metadata, transcript=Transcript(video_id=video_id, language="und", source="captions"))

    tab_frames = extract_tab_ocr(args.url, start, end, fps=args.fps, crop_bottom_fraction=args.crop)

    md = build_tab_markdown(source, start, end, tab_frames)
    report_path = args.report_path or f"reports/youtube/{video_id}.tab.md"
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(md, encoding="utf-8")
    logger.info("Αναφορά ταμπλατούρας γράφτηκε στο %s (%d frames)", report_path, len(tab_frames))
    print(md)
    return 0


def cmd_lesson(args: argparse.Namespace) -> int:
    from .pipeline import build_lesson_report
    from .report import build_lesson_markdown

    video_id = extract_video_id(args.url)
    start = parse_timecode(args.start)
    end = parse_timecode(args.end)
    if end <= start:
        logger.error("Το --end πρέπει να είναι μετά το --start")
        return 1

    source, matches, tab_frames = build_lesson_report(
        args.url,
        start,
        end,
        max_related=args.max_related,
        fps=args.fps,
        crop_bottom_fraction=args.crop,
        asr_model=args.asr_model,
        library_dir=args.library_dir,
    )

    md = build_lesson_markdown(source, start, end, matches, tab_frames)
    report_path = args.report_path or f"reports/youtube/{video_id}.lesson.md"
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(md, encoding="utf-8")
    logger.info("Αναφορά μαθήματος γράφτηκε στο %s", report_path)
    print(md)
    return 0


def cmd_library_list(args: argparse.Namespace) -> int:
    ids = list_video_ids(library_dir=args.library_dir)
    if not ids:
        print("Η βιβλιοθήκη είναι άδεια.")
        return 0
    for vid in ids:
        analysis = load_analysis(vid, library_dir=args.library_dir)
        title = analysis.metadata.title if analysis else "?"
        print(f"{vid}  {title}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="youtube_analyzer — ανάλυση, σύγκριση και ελληνικοί υπότιτλοι για YouTube βίντεο")
    parser.add_argument("--library-dir", default=DEFAULT_LIBRARY_DIR, help="Φάκελος τοπικής βιβλιοθήκης αναλύσεων")
    sub = parser.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser("analyze", help="Πλήρης ανάλυση + περίληψη βίντεο")
    p_analyze.add_argument("url", help="YouTube URL ή video ID")
    p_analyze.add_argument("--report", dest="report_path", default=None, help="Path εξόδου Markdown")
    p_analyze.add_argument("--asr-model", default="small", help="Μέγεθος μοντέλου Whisper για ASR fallback")
    p_analyze.add_argument("--no-translate", action="store_true", help="Μη μεταφράζεις την περίληψη στα ελληνικά")
    p_analyze.add_argument("--no-library", action="store_true", help="Μην αποθηκεύσεις στη βιβλιοθήκη")
    p_analyze.set_defaults(func=cmd_analyze)

    p_subs = sub.add_parser("subtitles", help="Δημιουργία ελληνικών υποτίτλων (.srt)")
    p_subs.add_argument("url", help="YouTube URL ή video ID")
    p_subs.add_argument("--out", default=None, help="Path εξόδου .srt")
    p_subs.add_argument("--asr-model", default="small", help="Μέγεθος μοντέλου Whisper για ASR fallback")
    p_subs.set_defaults(func=cmd_subtitles)

    p_compare = sub.add_parser("compare", help="Σύγκριση αποσπάσματος έναντι της βιβλιοθήκης")
    p_compare.add_argument("url", help="YouTube URL ή video ID")
    p_compare.add_argument("--start", required=True, help="Αρχή αποσπάσματος (π.χ. 12:34)")
    p_compare.add_argument("--end", required=True, help="Τέλος αποσπάσματος (π.χ. 15:10)")
    p_compare.add_argument("--top", type=int, default=10, help="Μέγιστος αριθμός αποτελεσμάτων")
    p_compare.add_argument("--min-score", type=float, default=0.12, help="Ελάχιστο σκορ ομοιότητας [0,1]")
    p_compare.add_argument("--report", dest="report_path", default=None, help="Path εξόδου Markdown")
    p_compare.add_argument("--asr-model", default="small", help="Μέγεθος μοντέλου Whisper για ASR fallback")
    p_compare.set_defaults(func=cmd_compare)

    p_tab = sub.add_parser("tab", help="Ανάγνωση (OCR) ταμπλατούρας από την οθόνη, συγχρονισμένη με τον χρόνο")
    p_tab.add_argument("url", help="YouTube URL ή video ID")
    p_tab.add_argument("--start", required=True, help="Αρχή αποσπάσματος (π.χ. 2:25)")
    p_tab.add_argument("--end", required=True, help="Τέλος αποσπάσματος (π.χ. 3:00)")
    p_tab.add_argument("--fps", type=float, default=1.0, help="Ρυθμός δειγματοληψίας frames για OCR")
    p_tab.add_argument("--crop", type=float, default=0.5, help="Ποσοστό κάτω μέρους της εικόνας για OCR (0-1)")
    p_tab.add_argument("--report", dest="report_path", default=None, help="Path εξόδου Markdown")
    p_tab.set_defaults(func=cmd_tab)

    p_lesson = sub.add_parser(
        "lesson",
        help="Πλήρες μάθημα: OCR ταμπλατούρα συγχρονισμένη με την εικόνα + αυτόματη αναζήτηση/σύγκριση με σχετικά βίντεο",
    )
    p_lesson.add_argument("url", help="YouTube URL ή video ID")
    p_lesson.add_argument("--start", required=True, help="Αρχή αποσπάσματος (π.χ. 2:25)")
    p_lesson.add_argument("--end", required=True, help="Τέλος αποσπάσματος (π.χ. 3:00)")
    p_lesson.add_argument("--max-related", type=int, default=5, help="Πλήθος σχετικών βίντεο προς αναζήτηση/ανάλυση")
    p_lesson.add_argument("--fps", type=float, default=1.0, help="Ρυθμός δειγματοληψίας frames για OCR")
    p_lesson.add_argument("--crop", type=float, default=0.5, help="Ποσοστό κάτω μέρους της εικόνας για OCR (0-1)")
    p_lesson.add_argument("--asr-model", default="small", help="Μέγεθος μοντέλου Whisper για ASR fallback")
    p_lesson.add_argument("--report", dest="report_path", default=None, help="Path εξόδου Markdown")
    p_lesson.set_defaults(func=cmd_lesson)

    p_lib = sub.add_parser("library-list", help="Λίστα αναλυμένων βίντεο στη βιβλιοθήκη")
    p_lib.set_defaults(func=cmd_library_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
