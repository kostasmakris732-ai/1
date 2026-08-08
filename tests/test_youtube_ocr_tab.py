from youtube_analyzer.ocr_tab import merge_tab_samples


def test_merge_tab_samples_collapses_stable_consecutive_frames():
    samples = [
        (0.0, "e|-0-2-3-|\nB|-1-3-1-|"),
        (1.0, "e|-0-2-3-|\nB|-1-3-1-|"),
        (2.0, "e|-0-2-3-|\nB|-1-3-1-|"),
        (3.0, "e|-5-7-8-|\nB|-6-8-6-|"),
        (4.0, "e|-5-7-8-|\nB|-6-8-6-|"),
    ]
    frames = merge_tab_samples(samples, frame_duration=1.0)
    assert len(frames) == 2
    assert frames[0].start == 0.0 and frames[0].end == 3.0
    assert "0-2-3" in frames[0].text
    assert frames[1].start == 3.0 and frames[1].end == 5.0
    assert "5-7-8" in frames[1].text


def test_merge_tab_samples_tolerates_minor_ocr_noise():
    # Μικρές διαφορές OCR (π.χ. "l" vs "1") στο ίδιο tab πρέπει να συνενωθούν.
    samples = [
        (0.0, "e|-0-2-3-|"),
        (1.0, "e|-O-2-3-|"),  # OCR typo: O αντί 0
        (2.0, "e|-0-2-3-|"),
    ]
    frames = merge_tab_samples(samples, frame_duration=1.0)
    assert len(frames) == 1
    assert frames[0].start == 0.0 and frames[0].end == 3.0


def test_merge_tab_samples_filters_short_noise():
    samples = [(0.0, ""), (1.0, "  "), (2.0, "x"), (3.0, "e|-0-2-3-|")]
    frames = merge_tab_samples(samples, frame_duration=1.0, min_chars=4)
    assert len(frames) == 1
    assert frames[0].start == 3.0


def test_merge_tab_samples_empty_input():
    assert merge_tab_samples([]) == []


def test_merge_tab_samples_unsorted_input_is_sorted():
    samples = [
        (2.0, "e|-5-7-8-|"),
        (0.0, "e|-0-2-3-|"),
        (1.0, "e|-0-2-3-|"),
    ]
    frames = merge_tab_samples(samples, frame_duration=1.0)
    assert [round(f.start) for f in frames] == [0, 2]
