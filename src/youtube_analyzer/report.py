"""Παραγωγή αναφορών Markdown (ελληνικά) από αποτελέσματα ανάλυσης/σύγκρισης.

Καθαρή λογική — δέχεται ήδη υπολογισμένα αντικείμενα (VideoAnalysis,
SegmentMatch), δεν κάνει I/O.
"""

from __future__ import annotations

from .models import SegmentMatch, VideoAnalysis
from .timecode import format_timecode, youtube_timestamp_link

SOURCE_LABEL = {"captions": "υπάρχοντες υπότιτλοι/CC", "asr": "αυτόματη αναγνώριση ομιλίας (ASR)"}


def build_analysis_markdown(analysis: VideoAnalysis) -> str:
    meta = analysis.metadata
    t = analysis.transcript

    lines = [
        f"# {meta.title or meta.video_id}",
        "",
        f"_Κανάλι: **{meta.channel or 'άγνωστο'}**",
    ]
    if meta.upload_date:
        lines[-1] += f" · Ημ/νία ανάρτησης: {meta.upload_date[:4]}-{meta.upload_date[4:6]}-{meta.upload_date[6:]}"
    lines[-1] += f" · Διάρκεια: {format_timecode(meta.duration_s, always_hours=True)}_"
    lines += [
        "",
        f"**Βίντεο:** {meta.url}",
        f"**Γλώσσα transcript:** `{t.language}` · **Πηγή:** {SOURCE_LABEL.get(t.source, t.source)}",
        "",
        "---",
        "",
        "## 📋 Περίληψη ανά θεματική ενότητα",
        "",
    ]

    if not analysis.topics:
        lines.append("_Δεν βρέθηκε αρκετό περιεχόμενο transcript για εξαγωγή θεματικών ενοτήτων._")
    for topic in analysis.topics:
        link = youtube_timestamp_link(meta.video_id, topic.start)
        span = f"{format_timecode(topic.start)}–{format_timecode(topic.end)}"
        lines.append(f"### [{span}]({link}) — {topic.title}")
        for bullet in topic.bullets:
            lines.append(f"- {bullet}")
        lines.append("")

    if analysis.resources:
        lines += ["---", "", "## 🔗 Πόροι/links από την περιγραφή", ""]
        for label, url in analysis.resources:
            lines.append(f"- [{label}]({url})")
        lines.append("")

    lines += ["---", "", f"_Παράχθηκε αυτόματα από youtube_analyzer · {len(t.segments)} segments transcript._"]
    return "\n".join(lines)


def build_compare_markdown(source: VideoAnalysis, start: float, end: float, matches: list[SegmentMatch]) -> str:
    meta = source.metadata
    span = f"{format_timecode(start)}–{format_timecode(end)}"
    source_link = youtube_timestamp_link(meta.video_id, start)

    lines = [
        f"# Σύγκριση αποσπάσματος — {meta.title or meta.video_id}",
        "",
        f"**Πηγή:** [{span}]({source_link}) · {meta.url}",
        "",
        "---",
        "",
    ]

    if not matches:
        lines += [
            "## Δεν βρέθηκαν όμοια αποσπάσματα σε άλλα βίντεο της βιβλιοθήκης.",
            "",
            "_Χρειάζεται να έχουν πρώτα αναλυθεί (`analyze`) και άλλα βίντεο ώστε να "
            "υπάρχουν στη βιβλιοθήκη για σύγκριση._",
        ]
        return "\n".join(lines)

    lines.append(f"## 🔎 {len(matches)} όμοια αποσπάσματα σε άλλα βίντεο")
    lines.append("")
    lines.append("| Βίντεο | Τμήμα | Ομοιότητα | Απόσπασμα |")
    lines.append("|---|---|---|---|")
    for m in matches:
        link = youtube_timestamp_link(m.video_id, m.start)
        m_span = f"{format_timecode(m.start)}–{format_timecode(m.end)}"
        lines.append(f"| {m.title or m.video_id} | [{m_span}]({link}) | {m.score:.0%} | {m.snippet} |")

    lines += ["", "---", "", "_Η ομοιότητα υπολογίζεται με TF-IDF (char n-grams) πάνω στο transcript κειμένο, όχι νοηματική επαλήθευση από μοντέλο γλώσσας._"]
    return "\n".join(lines)
