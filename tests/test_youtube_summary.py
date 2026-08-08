from youtube_analyzer.models import TextChunk
from youtube_analyzer.summary import build_topics, extract_resources, split_sentences, top_sentences


def test_split_sentences_basic():
    text = "Αυτό είναι το πρώτο. Αυτό είναι το δεύτερο! Και τρίτο;"
    result = split_sentences(text)
    assert result == ["Αυτό είναι το πρώτο.", "Αυτό είναι το δεύτερο!", "Και τρίτο;"]


def test_split_sentences_empty():
    assert split_sentences("") == []


def test_top_sentences_returns_all_when_fewer_than_max():
    text = "Πρώτη πρόταση. Δεύτερη πρόταση."
    assert top_sentences(text, max_sentences=5) == ["Πρώτη πρόταση.", "Δεύτερη πρόταση."]


def test_top_sentences_preserves_original_order():
    text = (
        "Η γάτα κάθεται στο χαλί. "
        "Ο καιρός σήμερα είναι ωραίος. "
        "Η γάτα και ο σκύλος παίζουν μαζί στο χαλί. "
        "Ο ήλιος λάμπει. "
        "Η γάτα, ο σκύλος και το χαλί είναι το κύριο θέμα εδώ."
    )
    result = top_sentences(text, max_sentences=2)
    assert len(result) == 2
    positions = [text.index(s) for s in result]
    assert positions == sorted(positions)
    # Οι προτάσεις με τις πιο επαναλαμβανόμενες λέξεις (γάτα/χαλί) πρέπει να κερδίζουν.
    assert any("γάτα" in s for s in result)


def test_build_topics_from_chunks():
    chunks = [
        TextChunk("v1", 0, 45, "Σήμερα μιλάμε για μηχανική μάθηση. Η μηχανική μάθηση είναι σημαντική."),
        TextChunk("v1", 45, 90, "Τώρα περνάμε σε νευρωνικά δίκτυα. Τα νευρωνικά δίκτυα είναι ισχυρά."),
    ]
    topics = build_topics(chunks, max_bullets_per_topic=2)
    assert len(topics) == 2
    assert topics[0].start == 0 and topics[0].end == 45
    assert topics[0].title.startswith("Σήμερα μιλάμε")
    assert topics[1].start == 45 and topics[1].end == 90


def test_build_topics_skips_empty_chunks():
    chunks = [TextChunk("v1", 0, 10, "   ")]
    assert build_topics(chunks) == []


def test_extract_resources_labels_from_prefix():
    description = (
        "Καλωσήρθατε στο κανάλι!\n"
        "Site: https://example.com/page\n"
        "Κώδικας στο GitHub -> https://github.com/example/repo\n"
        "Απλά ένα link χωρίς ετικέτα: https://noext.example.org/x\n"
    )
    resources = extract_resources(description)
    urls = [u for _, u in resources]
    assert "https://example.com/page" in urls
    assert "https://github.com/example/repo" in urls
    label_by_url = {url: label for label, url in resources}
    assert label_by_url["https://example.com/page"] == "Site"


def test_extract_resources_falls_back_to_domain():
    description = "https://www.example.org/deep/path"
    resources = extract_resources(description)
    assert resources == [("example.org", "https://www.example.org/deep/path")]


def test_extract_resources_no_urls():
    assert extract_resources("Δεν υπάρχουν links εδώ.") == []
