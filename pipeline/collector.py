import gzip

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET


USER_AGENT = "WorldPulse/6.0"


def _text(element):
    if element is None:
        return ""

    return " ".join(
        part.strip()
        for part in element.itertext()
        if part and part.strip()
    ).strip()


def _parse_date(value):
    if not value:
        return None

    value = str(value).strip()

    try:
        dt = parsedate_to_datetime(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc).isoformat()

    except (TypeError, ValueError, OverflowError):
        pass

    try:
        dt = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc).isoformat()

    except (TypeError, ValueError):
        return None


def _local_name(tag):
    return tag.rsplit("}", 1)[-1]


def _child(element, names):
    for child in list(element):
        if _local_name(child.tag) in names:
            return child

    return None


def _items(root):
    result = []

    for element in root.iter():
        if _local_name(element.tag) in {"item", "entry"}:
            result.append(element)

    return result


def _extract_article(item, source, *, first_seen_at=None):
    title = _text(
        _child(item, {"title"})
    )

    summary = _text(
        _child(
            item,
            {"description", "summary", "content"}
        )
    )

    link_element = _child(
        item,
        {"link"}
    )

    url = ""

    if link_element is not None:
        url = (
            link_element.attrib.get("href")
            or _text(link_element)
        ).strip()

    date_element = _child(
        item,
        {
            "pubDate",
            "published",
            "updated",
            "date",
        }
    )

    published_at = _parse_date(
        _text(date_element)
    )

    result = {
        "title": title,
        "summary": summary,
        "source": source,
        "url": url,
        "published_at": published_at,
    }

    if first_seen_at is not None:
        result["first_seen_at"] = first_seen_at

    return result


def fetch_feed(
    feed_url,
    source=None,
    timeout=15,
):
    if not isinstance(feed_url, str):
        return []

    feed_url = feed_url.strip()

    if not feed_url:
        return []

    parsed = urlparse(feed_url)

    if parsed.scheme not in {"http", "https"}:
        return []

    try:
        request = Request(
            feed_url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": (
                    "application/rss+xml, "
                    "application/atom+xml, "
                    "application/xml, "
                    "text/xml"
                ),
            },
        )

        with urlopen(
            request,
            timeout=timeout,
        ) as response:
            data = response.read()

            first_seen_at = None

        if data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)

        root = ET.fromstring(data)

    except Exception:
        return []

    if source is None:
        source = parsed.hostname or "Unknown"

    source = str(source).strip()

    if not source:
        source = "Unknown"

    articles = []

    for item in _items(root):
        article = _extract_article(
            item,
            source,
            first_seen_at=first_seen_at,
        )

        if article["title"]:
            articles.append(article)

    return articles


def collect_feeds(
    feeds,
    timeout=15,
):
    if not isinstance(
        feeds,
        (list, tuple),
    ):
        return []

    articles = []

    for feed in feeds:
        if isinstance(feed, dict):
            url = feed.get("url")
            source = feed.get("source")
        else:
            url = feed
            source = None

        articles.extend(
            fetch_feed(
                url,
                source=source,
                timeout=timeout,
            )
        )

    return articles


def deduplicate_articles(articles):
    if not isinstance(articles, list):
        return []

    result = []
    seen = set()

    for article in articles:

        if not isinstance(article, dict):
            continue

        url = str(
            article.get("url") or ""
        ).strip()

        if url:
            key = ("url", url)
        else:
            key = (
                "title",
                str(
                    article.get("source") or ""
                ).strip().lower(),
                str(
                    article.get("title") or ""
                ).strip().lower(),
            )

        if key in seen:
            continue

        seen.add(key)
        result.append(article)

    return result


def collect(
    feeds,
    timeout=15,
):
    articles = collect_feeds(
        feeds,
        timeout=timeout,
    )

    return deduplicate_articles(
        articles
    )
