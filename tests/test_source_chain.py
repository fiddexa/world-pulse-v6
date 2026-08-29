from pipeline.source_chain import (
    analyze_source_chain,
    count_independent_sources,
    independent_source_groups,
    is_independent,
    same_origin,
    same_source,
    source_chain_summary,
)


def article(
    source,
    *,
    origin_source=None,
    derivation=None,
):
    result = {
        "title": "Test event",
        "source": source,
    }

    if origin_source is not None:
        result["origin_source"] = origin_source

    if derivation is not None:
        result["derivation"] = derivation

    return result


def test_same_publisher_is_not_independent():
    a = article("Reuters")
    b = article("Reuters")

    assert same_source(a, b)
    assert not is_independent(a, b)


def test_different_publishers_are_independent():
    a = article("Reuters")
    b = article("BBC")

    assert not same_source(a, b)
    assert is_independent(a, b)


def test_same_origin_is_not_independent():
    a = article(
        "Reuters",
        origin_source="official-government-statement",
        derivation="direct_report",
    )

    b = article(
        "BBC",
        origin_source="official-government-statement",
        derivation="republished",
    )

    assert same_origin(a, b)
    assert not is_independent(a, b)


def test_three_publishers_from_one_origin_count_as_one():
    articles = [
        article(
            "Reuters",
            origin_source="official-statement",
            derivation="direct_report",
        ),
        article(
            "BBC",
            origin_source="official-statement",
            derivation="republished",
        ),
        article(
            "AP",
            origin_source="official-statement",
            derivation="aggregated",
        ),
    ]

    assert count_independent_sources(articles) == 1


def test_two_distinct_origins_count_as_two():
    articles = [
        article(
            "Reuters",
            origin_source="source-a",
            derivation="direct_report",
        ),
        article(
            "BBC",
            origin_source="source-a",
            derivation="republished",
        ),
        article(
            "AP",
            origin_source="source-b",
            derivation="direct_report",
        ),
    ]

    assert count_independent_sources(articles) == 2


def test_same_publisher_without_origin_counts_once():
    articles = [
        article("Reuters"),
        article("Reuters"),
        article("Reuters"),
    ]

    assert count_independent_sources(articles) == 1


def test_unknown_provenance_does_not_create_false_shared_origin():
    articles = [
        article("Reuters"),
        article("BBC"),
    ]

    assert count_independent_sources(articles) == 2


def test_independent_source_groups_group_known_origins():
    articles = [
        article(
            "Reuters",
            origin_source="origin-a",
            derivation="direct_report",
        ),
        article(
            "BBC",
            origin_source="origin-a",
            derivation="republished",
        ),
        article(
            "AP",
            origin_source="origin-b",
            derivation="direct_report",
        ),
    ]

    groups = independent_source_groups(articles)

    assert len(groups) == 2
    assert sorted(
        len(group)
        for group in groups
    ) == [1, 2]


def test_summary_reports_high_independence():
    articles = [
        article(
            "Reuters",
            origin_source="origin-a",
            derivation="direct_report",
        ),
        article(
            "BBC",
            origin_source="origin-b",
            derivation="direct_report",
        ),
        article(
            "AP",
            origin_source="origin-c",
            derivation="direct_report",
        ),
    ]

    summary = source_chain_summary(articles)

    assert summary["article_count"] == 3
    assert summary["independent_sources"] == 3
    assert summary["independence_confidence"] == "HIGH"
def test_summary_handles_invalid_input():
    summary = source_chain_summary(
        [None, {}, "invalid"]
    )

    assert summary["article_count"] == 1
    assert summary["independent_sources"] == 0


def test_analyze_event_is_non_mutating():
    event = {
        "articles": [
            article("Reuters"),
            article("BBC"),
        ]
    }

    before = dict(event)

    result = analyze_source_chain(event)

    assert event == before
    assert result["independent_sources"] == 2
