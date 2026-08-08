from youtube_analyzer.models import TranscriptSegment
from youtube_analyzer.subtitles import segments_to_srt, segments_to_vtt


def _segs():
    return [
        TranscriptSegment(start=0.0, end=2.5, text="Γεια σας και καλώς ήρθατε."),
        TranscriptSegment(start=2.5, end=5.0, text="Σήμερα θα δούμε ένα σημαντικό θέμα."),
        TranscriptSegment(start=5.0, end=5.2, text="   "),  # κενό — πρέπει να παραλειφθεί
    ]


def test_segments_to_srt_basic_structure():
    srt = segments_to_srt(_segs())
    assert "1\n00:00:00,000 --> 00:00:02,500\n" in srt
    assert "Γεια σας και καλώς ήρθατε." in srt
    assert srt.count("-->") == 2  # το κενό segment παραλείφθηκε


def test_segments_to_srt_empty_segments_skipped():
    srt = segments_to_srt([TranscriptSegment(0, 1, "")])
    assert srt == ""


def test_segments_to_vtt_has_header():
    vtt = segments_to_vtt(_segs())
    assert vtt.startswith("WEBVTT")
    assert "00:00:00.000 --> 00:00:02.500" in vtt


def test_min_cue_duration_enforced():
    # Πολύ σύντομο segment (0.1s) πρέπει να επεκταθεί στην ελάχιστη διάρκεια.
    segs = [TranscriptSegment(start=10.0, end=10.1, text="Ναι.")]
    srt = segments_to_srt(segs)
    assert "00:00:10,000 --> 00:00:11,000" in srt


def test_long_text_wraps_into_multiple_lines():
    long_text = " ".join(["λέξη"] * 40)
    segs = [TranscriptSegment(start=0, end=5, text=long_text)]
    srt = segments_to_srt(segs)
    body = srt.split("\n", 2)[2]
    first_cue_text = body.split("\n\n")[0]
    lines = first_cue_text.strip().split("\n")
    assert len(lines) <= 2
    assert all(len(line) <= 60 for line in lines)


def test_very_long_text_splits_into_multiple_sequential_cues():
    long_text = " ".join(["λέξη"] * 60)  # πολύ περισσότερο από 2 γραμμές των 42 χαρακτήρων
    segs = [TranscriptSegment(start=100.0, end=110.0, text=long_text)]
    srt = segments_to_srt(segs)

    cue_count = srt.count("-->")
    assert cue_count > 1, "Το υπερβολικά μακρύ κείμενο έπρεπε να σπάσει σε πολλά cues"

    # Κάθε γραμμή κάθε cue πρέπει να σέβεται το όριο πλάτους.
    for block in srt.strip().split("\n\n"):
        text_lines = block.split("\n")[2:]
        assert all(len(line) <= 42 for line in text_lines)

    # Τα cues πρέπει να καλύπτουν διαδοχικά, μη-επικαλυπτόμενα χρονικά παράθυρα
    # μέσα στο αρχικό διάστημα [100, 110] του segment.
    timestamps = [line for line in srt.splitlines() if "-->" in line]
    assert len(timestamps) == cue_count
    first_start = timestamps[0].split(" --> ")[0]
    last_end = timestamps[-1].split(" --> ")[1]
    assert first_start == "00:01:40,000"
    assert last_end == "00:01:50,000"
