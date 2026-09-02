"""
AROUND THE MAIN v6 - Source Connector Layer

Provides a common interface for source-specific ingestion.

Connector types:
- rss
- api
- licensed

The connector layer is intentionally separated from:
- source reputation;
- editorial verification;
- intelligence;
- ranking;
- publication.

Connectors return normalized article dictionaries.
"""

from datetime import datetime, timezone
from typing import Any, Callable


CONNECTOR_RSS = "rss"
CONNECTOR_API = "api"
CONNECTOR_LICENSED = "licensed"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def normalize_connector_article(
    article: Any,
    *,
    source: str,
    first_seen_at: datetime | None = None,
) -> dict:
    """
    Convert connector output into the common AROUND THE MAIN article format.
    """

    if not isinstance(article, dict):
        return {}

    result = dict(article)

    result["source"] = (
        _safe_text(result.get("source"))
        or source
    )

    if first_seen_at is None:
        existing_first_seen = result.get("first_seen_at")

        if existing_first_seen:
            first_seen_at = existing_first_seen
        else:
            published_at = result.get("published_at")

            if published_at:
                result["first_seen_at"] = str(
                    published_at
                ).strip()

    if (
        first_seen_at is not None
        and not result.get("first_seen_at")
    ):
        if isinstance(first_seen_at, datetime):
            result["first_seen_at"] = (
                first_seen_at.isoformat()
            )
        else:
            result["first_seen_at"] = str(
                first_seen_at
            ).strip()

    return result


class SourceConnector:
    """
    Base source connector.

    Concrete connectors should implement collect().
    """

    connector_type = None

    def __init__(
        self,
        source: str,
        *,
        enabled: bool = True,
    ):
        self.source = source
        self.enabled = bool(enabled)

    def collect(self) -> list[dict]:
        raise NotImplementedError


class RSSConnector(SourceConnector):
    """
    Adapter around the existing RSS/Atom collector.

    This class does not perform HTTP itself. The existing collector
    remains responsible for RSS/Atom transport and parsing.
    """

    connector_type = CONNECTOR_RSS

    def __init__(
        self,
        source: str,
        feeds: list[dict],
        collector: Callable,
        *,
        timeout: int = 15,
    ):
        super().__init__(source)
        self.feeds = list(feeds or [])
        self.collector = collector
        self.timeout = timeout

    def collect(self) -> list[dict]:
        if not self.enabled or not self.feeds:
            return []

        articles = self.collector(
            self.feeds,
            timeout=self.timeout,
        )

        return [
            normalize_connector_article(
                article,
                source=self.source,
            )
            for article in articles
            if isinstance(article, dict)
        ]


class APIConnector(SourceConnector):
    """
    Base connector for authenticated or public source APIs.

    The actual HTTP implementation is supplied as a callable so
    credentials and vendor-specific logic stay outside the core.
    """

    connector_type = CONNECTOR_API

    def __init__(
        self,
        source: str,
        fetcher: Callable,
        *,
        enabled: bool = True,
    ):
        super().__init__(
            source,
            enabled=enabled,
        )
        self.fetcher = fetcher

    def collect(self) -> list[dict]:
        if not self.enabled:
            return []

        result = self.fetcher()

        if not isinstance(result, list):
            return []

        first_seen_at = utc_now()

        return [
            normalize_connector_article(
                article,
                source=self.source,
                first_seen_at=first_seen_at,
            )
            for article in result
            if isinstance(article, dict)
        ]


class LicensedConnector(SourceConnector):
    """
    Placeholder for licensed feeds such as Reuters/AP.

    No endpoint or credentials are embedded in source code.
    Production activation is explicit.
    """

    connector_type = CONNECTOR_LICENSED

    def __init__(
        self,
        source: str,
        *,
        enabled: bool = False,
    ):
        super().__init__(
            source,
            enabled=enabled,
        )

    def collect(self) -> list[dict]:
        if not self.enabled:
            return []

        raise RuntimeError(
            f"Licensed connector for {self.source} "
            "requires an approved production integration."
        )


def build_connectors(
    *,
    feed_registry,
    connector_registry,
    collector,
    timeout=15,
):
    """
    Build enabled source connectors from configuration.

    Only connectors explicitly marked enabled are instantiated.
    """

    if not isinstance(feed_registry, dict):
        return []

    if not isinstance(connector_registry, dict):
        return []

    connectors = []

    for source, config in connector_registry.items():
        if not isinstance(config, dict):
            continue

        if config.get("enabled") is not True:
            continue

        connector_type = config.get("type")

        if connector_type == CONNECTOR_RSS:
            feeds = feed_registry.get(source, [])

            if not isinstance(feeds, list) or not feeds:
                continue

            connectors.append(
                RSSConnector(
                    source,
                    feeds,
                    collector,
                    timeout=timeout,
                )
            )

        elif connector_type == CONNECTOR_API:
            fetcher = config.get("fetcher")

            if callable(fetcher):
                connectors.append(
                    APIConnector(
                        source,
                        fetcher,
                    )
                )

        elif connector_type == CONNECTOR_LICENSED:
            connectors.append(
                LicensedConnector(
                    source,
                    enabled=True,
                )
            )

    return connectors


def collect_from_connectors(connectors):
    """
    Collect articles from all enabled connectors.

    A failure in one connector must not discard successful
    results from other connectors.
    """

    if not isinstance(connectors, (list, tuple)):
        return []

    articles = []

    for connector in connectors:
        if not callable(
            getattr(connector, "collect", None)
        ):
            continue

        try:
            result = connector.collect()
        except Exception:
            continue

        if isinstance(result, list):
            articles.extend(
                article
                for article in result
                if isinstance(article, dict)
            )

    return articles
