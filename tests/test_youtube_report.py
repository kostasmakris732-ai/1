from youtube_analyzer.models import (
    SegmentMatch,
    TabFrame,
    TextChunk,
    Transcript,
    TranscriptSegment,
    TopicSection,
    VideoAnalysis,
    VideoMetadata,
)
from youtube_analyzer.report import (
    build_analysis_markdown,
    build_compare_markdown,
    build_lesson_markdown,
    build_tab_markdown,
)


def _analysis():
    metadata = VideoMetadata(
        video_id="abc12345678",
        url="https://youtu.be/abc12345678",
        title="Δοκιμαστικό Βίντεο",
        channel="Κανάλι Δοκιμής",
        duration_s=125,
        upload_date="20260101",
        description="Site: https://example.com",
    )
    transcript = Transcript(
        video_id="abc12345678",
        language="el",
        source="captions",
        segments=[TranscriptSegment(0, 5, "Γεια σας.")],
    )
    chunks = [TextChunk("abc12345678", 0, 45, "Γεια σας.")]
    topics = [TopicSection(title="Εισαγωγή", start=0, end=45, bullets=["Καλωσορίσατε.", "Ξεκινάμε."])]
    return VideoAnalysis(metadata=metadata, transcript=transcript, chunks=chunks, topics=topics, resources=[("Site", "https://example.com")])


def test_build_analysis_markdown_contains_key_sections():
    md = build_analysis_markdown(_analysis())
    assert "# Δοκιμαστικό Βίντεο" in md
    assert "Κανάλι Δοκιμής" in md
    assert "## 📋 Περίληψη ανά θεματική ενότητα" in md
    assert "Εισαγωγή" in md
    assert "Καλωσορίσατε." in md
    assert "## 🔗 Πόροι/links από την περιγραφή" in md
    assert "https://example.com" in md
    assert "captions" not in md or "υπότιτλοι" in md  # πρέπει να εμφανίζεται η ελληνική ετικέτα πηγής


def test_build_compare_markdown_with_matches():
    source = _analysis()
    matches = [
        SegmentMatch(video_id="other0001a", title="Άλλο Βίντεο", start=30, end=60, score=0.42, snippet="κάποιο απόσπασμα κειμένου"),
    ]
    md = build_compare_markdown(source, start=0, end=45, matches=matches)
    assert "Άλλο Βίντεο" in md
    assert "42%" in md
    assert "κάποιο απόσπασμα κειμένου" in md


def test_build_compare_markdown_no_matches():
    md = build_compare_markdown(_analysis(), start=0, end=45, matches=[])
    assert "Δεν βρέθηκαν" in md


def test_build_tab_markdown_with_frames():
    tab_frames = [
        TabFrame(start=145, end=150, text="e|-0-2-3-|\nB|-1-3-1-|"),
        TabFrame(start=150, end=160, text="e|-5-7-8-|\nB|-6-8-6-|"),
    ]
    md = build_tab_markdown(_analysis(), start=145, end=180, tab_frames=tab_frames)
    assert "Ταμπλατούρα (OCR)" in md
    assert "e|-0-2-3-|" in md
    assert "e|-5-7-8-|" in md
    assert "```" in md
    assert "youtu.be/abc12345678?t=145s" in md


def test_build_tab_markdown_no_frames():
    md = build_tab_markdown(_analysis(), start=145, end=180, tab_frames=[])
    assert "Δεν εντοπίστηκε" in md


def test_build_lesson_markdown_combines_tab_and_matches():
    tab_frames = [TabFrame(start=145, end=150, text="e|-0-2-3-|")]
    matches = [
        SegmentMatch(video_id="other0001a", title="Σχετικό Μάθημα", start=30, end=60, score=0.5, snippet="ίδιο riff εδώ"),
    ]
    md = build_lesson_markdown(_analysis(), start=145, end=180, matches=matches, tab_frames=tab_frames)
    assert "Μάθημα:" in md
    assert "🎸" in md
    assert "e|-0-2-3-|" in md
    assert "Σχετικό Μάθημα" in md
    assert "50%" in md
    assert "ίδιο riff εδώ" in md


def test_build_lesson_markdown_no_tab_no_matches():
    md = build_lesson_markdown(_analysis(), start=145, end=180, matches=[], tab_frames=[])
    assert "Δεν εντοπίστηκε" in md
    assert "Δεν βρέθηκαν" in md
