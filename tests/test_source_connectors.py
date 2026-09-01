from pipeline.source_connectors import (
    APIConnector,
    LicensedConnector,
    RSSConnector,
    build_connectors,
    collect_from_connectors,
)


def test_build_connectors_only_enables_configured_sources():
    feeds = {
        "un": [
            {
                "url": "https://example.com/un.xml",
                "source": "UN",
            }
        ],
        "imf": [],
    }

    registry = {
        "un": {
            "type": "rss",
            "enabled": True,
        },
        "imf": {
            "type": "rss",
            "enabled": False,
        },
    }

    connectors = build_connectors(
        feed_registry=feeds,
        connector_registry=registry,
        collector=lambda feeds, timeout=15: [],
    )

    assert len(connectors) == 1
    assert isinstance(connectors[0], RSSConnector)
    assert connectors[0].source == "un"


def test_api_connector_normalizes_articles():
    connector = APIConnector(
        "associated_press",
        lambda: [
            {
                "title": "Test AP article",
            }
        ],
    )

    articles = connector.collect()

    assert len(articles) == 1
    assert articles[0]["title"] == "Test AP article"
    assert articles[0]["source"] == "associated_press"
    assert articles[0]["first_seen_at"]


def test_licensed_connector_is_disabled_by_default():
    connector = LicensedConnector(
        "reuters",
        enabled=False,
    )

    assert connector.collect() == []


def test_collect_from_connectors_survives_connector_failure():
    class BrokenConnector:
        source = "broken"

        def collect(self):
            raise RuntimeError("failure")

    class WorkingConnector:
        source = "working"

        def collect(self):
            return [
                {
                    "title": "Working article",
                    "source": "working",
                }
            ]

    articles = collect_from_connectors(
        [
            BrokenConnector(),
            WorkingConnector(),
        ]
    )

    assert len(articles) == 1
    assert articles[0]["title"] == "Working article"
