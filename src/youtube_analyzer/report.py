"""Παραγωγή αναφορών Markdown (ελληνικά) από αποτελέσματα ανάλυσης/σύγκρισης.

Καθαρή λογική — δέχεται ήδη υπολογισμένα αντικείμενα (VideoAnalysis,
SegmentMatch), δεν κάνει I/O.
"""

from __future__ import annotations

from .models import SegmentMatch, TabFrame, VideoAnalysis
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


def build_tab_markdown(source: VideoAnalysis, start: float, end: float, tab_frames: list[TabFrame]) -> str:
    """Αναφορά με την ταμπλατούρα/notation που διαβάστηκε (OCR) από την οθόνη,
    ένα code block ανά σταθερό χρονικό διάστημα, με clickable timestamp link."""
    meta = source.metadata
    span = f"{format_timecode(start)}–{format_timecode(end)}"

    lines = [
        f"# Ταμπλατούρα (OCR) — {meta.title or meta.video_id}",
        "",
        f"**Απόσπασμα:** [{span}]({youtube_timestamp_link(meta.video_id, start)}) · {meta.url}",
        "",
        "> ⚠️ Η ταμπλατούρα διαβάστηκε αυτόματα (OCR) από την εικόνα του βίντεο. "
        "Μπορεί να περιέχει λάθη — έλεγξέ την ακούγοντας παράλληλα το κομμάτι.",
        "",
        "---",
        "",
    ]

    if not tab_frames:
        lines.append(
            "_Δεν εντοπίστηκε αναγνώσιμη ταμπλατούρα στην οθόνη για αυτό το διάστημα "
            "(ή το βίντεο δεν έχει tab overlay)._"
        )
        return "\n".join(lines)

    for frame in tab_frames:
        link = youtube_timestamp_link(meta.video_id, frame.start)
        f_span = f"{format_timecode(frame.start)}–{format_timecode(frame.end)}"
        lines.append(f"### [{f_span}]({link})")
        lines.append("```")
        lines.append(frame.text)
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def build_lesson_markdown(
    source: VideoAnalysis,
    start: float,
    end: float,
    matches: list[SegmentMatch],
    tab_frames: list[TabFrame],
) -> str:
    """Ενιαία αναφορά «μαθήματος»: ταμπλατούρα συγχρονισμένη με την εικόνα +
    πού αλλού αναλύεται το ίδιο απόσπασμα."""
    meta = source.metadata
    span = f"{format_timecode(start)}–{format_timecode(end)}"

    lines = [
        f"# Μάθημα: {meta.title or meta.video_id} — [{span}]({youtube_timestamp_link(meta.video_id, start)})",
        "",
        f"**Βίντεο:** {meta.url} · **Κανάλι:** {meta.channel or 'άγνωστο'}",
        "",
        "---",
        "",
        "## 🎸 Ταμπλατούρα (OCR, συγχρονισμένη με την εικόνα)",
        "",
    ]

    if not tab_frames:
        lines.append(
            "_Δεν εντοπίστηκε αναγνώσιμη ταμπλατούρα στην οθόνη για αυτό το διάστημα "
            "(ή το βίντεο δεν έχει tab overlay)._"
        )
    else:
        lines.append(
            "> ⚠️ Διαβάστηκε αυτόματα (OCR) από την εικόνα — μπορεί να περιέχει λάθη, "
            "έλεγξέ την ακούγοντας παράλληλα το κομμάτι."
        )
        lines.append("")
        for frame in tab_frames:
            link = youtube_timestamp_link(meta.video_id, frame.start)
            f_span = f"{format_timecode(frame.start)}–{format_timecode(frame.end)}"
            lines.append(f"**[{f_span}]({link})**")
            lines.append("```")
            lines.append(frame.text)
            lines.append("```")
            lines.append("")

    lines += ["---", "", "## 🔎 Πού αλλού αναλύεται αυτό το απόσπασμα", ""]
    if not matches:
        lines.append("_Δεν βρέθηκαν όμοια αποσπάσματα στα σχετικά βίντεο που εντοπίστηκαν._")
    else:
        lines.append("| Βίντεο | Τμήμα | Ομοιότητα | Απόσπασμα |")
        lines.append("|---|---|---|---|")
        for m in matches:
            link = youtube_timestamp_link(m.video_id, m.start)
            m_span = f"{format_timecode(m.start)}–{format_timecode(m.end)}"
            lines.append(f"| {m.title or m.video_id} | [{m_span}]({link}) | {m.score:.0%} | {m.snippet} |")

    lines += [
        "",
        "---",
        "",
        "_Τα σχετικά βίντεο εντοπίστηκαν αυτόματα με αναζήτηση στο YouTube βάσει "
        "του τίτλου του πηγαίου βίντεο· η ομοιότητα υπολογίζεται με TF-IDF πάνω στο transcript."
        "_",
    ]
    return "\n".join(lines)
