from youtube_analyzer.similarity import rank_by_similarity


def test_rank_by_similarity_finds_the_relevant_text():
    query = "Η αγορά μετοχών επηρεάζεται από τα επιτόκια της κεντρικής τράπεζας."
    corpus = [
        "Σήμερα μαγειρέψαμε μια συνταγή με ντομάτες και βασιλικό.",
        "Τα επιτόκια της κεντρικής τράπεζας επηρεάζουν άμεσα την αγορά μετοχών.",
        "Ο καιρός αύριο θα είναι ηλιόλουστος με λίγα σύννεφα.",
    ]
    ranked = rank_by_similarity(query, corpus, top_k=3, min_score=0.0)
    assert ranked[0].index == 1


def test_rank_by_similarity_respects_min_score():
    query = "εντελώς άσχετο κείμενο για μαγειρική"
    corpus = ["κβαντική φυσική και σωματίδια", "ιστορία της αρχαίας Ρώμης"]
    ranked = rank_by_similarity(query, corpus, top_k=10, min_score=0.9)
    assert ranked == []


def test_rank_by_similarity_empty_corpus():
    assert rank_by_similarity("query", [], top_k=5) == []


def test_rank_by_similarity_top_k_limits_results():
    query = "test test test"
    corpus = [f"test test test {i}" for i in range(20)]
    ranked = rank_by_similarity(query, corpus, top_k=5, min_score=0.0)
    assert len(ranked) == 5
