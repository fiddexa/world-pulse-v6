"""
WORLD PULSE v6 - Feed Health

Health checks for configured RSS/Atom feeds.

This module does not modify the collector and does not
control production scheduling.

It provides a deterministic health-check layer that can
be tested with an injected fetch function.
"""

from typing import Any, Callable


OK = "OK"
EMPTY = "EMPTY"
FAILED = "FAILED"


VALID_STATUSES = {
    OK,
    EMPTY,
    FAILED,
}


def check_feed(
    feed: Any,
    *,
    fetcher: Callable | None = None,
    timeout: int = 15,
) -> dict:
    """
    Check one configured feed.

    The fetcher must accept:

        fetcher(url, source=..., timeout=...)

    and return a list of articles.

    When no fetcher is supplied, pipeline.collector.fetch_feed
    is used.
    """

    if not isinstance(feed, dict):
        return {
            "url": "",
            "source": "",
            "status": FAILED,
            "article_count": 0,
        }

    url = str(
        feed.get("url") or ""
    ).strip()

    source = str(
        feed.get("source") or ""
    ).strip()

    if not url:
        return {
            "url": url,
            "source": source,
            "status": FAILED,
            "article_count": 0,
        }

    if fetcher is None:
        from pipeline.collector import fetch_feed

        fetcher = fetch_feed

    try:
        articles = fetcher(
            url,
            source=source or None,
            timeout=timeout,
        )

    except Exception:
        return {
            "url": url,
            "source": source,
            "status": FAILED,
            "article_count": 0,
        }

    if not isinstance(articles, list):
        return {
            "url": url,
            "source": source,
            "status": FAILED,
            "article_count": 0,
        }

    if not articles:
        return {
            "url": url,
            "source": source,
            "status": EMPTY,
            "article_count": 0,
        }

    return {
        "url": url,
        "source": source,
        "status": OK,
        "article_count": len(articles),
    }


def check_feeds(
    feeds: Any,
    *,
    fetcher: Callable | None = None,
    timeout: int = 15,
) -> list[dict]:
    """
    Check all supplied feeds independently.

    One failed feed does not prevent other feeds from
    being checked.
    """

    if not isinstance(
        feeds,
        (list, tuple),
    ):
        return []

    return [
        check_feed(
            feed,
            fetcher=fetcher,
            timeout=timeout,
        )
        for feed in feeds
    ]


def summarize_health(
    results: Any,
) -> dict:
    """
    Summarize feed health results.
    """

    if not isinstance(
        results,
        list,
    ):
        results = []

    summary = {
        "total": len(results),
        "ok": 0,
        "empty": 0,
        "failed": 0,
    }

    for result in results:
        if not isinstance(result, dict):
            continue

        status = result.get("status")

        if status == OK:
            summary["ok"] += 1
        elif status == EMPTY:
            summary["empty"] += 1
        elif status == FAILED:
            summary["failed"] += 1

    return summary
