import json
import logging
import re
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from abs_metadata_podium.models import BookMetadata, SeriesMetadata

BASE_URL = "https://podiumentertainment.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 10.0
MAX_RESULTS = 5

_SERIES_RE = re.compile(r"^(.*),\s*Book\s+([\d.,\s]+)$")
_HOURS_RE = re.compile(r"(\d+)\s*hr")
_MINUTES_RE = re.compile(r"(\d+)\s*min")

logger = logging.getLogger(__name__)


def search(
    query: str,
    author: str | None = None,
    session: requests.Session | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[BookMetadata]:
    session = session or requests.Session()
    search_term = f"{query} {author}" if author else query
    logger.debug("search(): query=%r author=%r -> search_term=%r", query, author, search_term)

    search_html = _fetch_search_page_html(search_term, session, timeout)
    candidates = _parse_search_results(search_html)
    logger.debug("search(): %d candidate(s) found: %s", len(candidates), candidates)
    if not candidates:
        logger.debug(
            "search(): no candidates matched - either Podium has no results for %r, "
            "or the search page's HTML structure no longer matches what this scraper expects",
            search_term,
        )

    results = []
    for url, title in candidates[:MAX_RESULTS]:
        try:
            logger.debug("search(): fetching detail page for %r: %s", title, url)
            detail_html = _fetch_detail_page_html(url, session, timeout)
            book = parse_detail_page(detail_html, url)
            logger.debug("search(): parsed metadata from %s: %s", url, book.to_dict())
            results.append(book)
        except Exception:
            logger.warning("Failed to fetch/parse detail page %s", url, exc_info=True)
    return results


def _fetch_search_page_html(query: str, session: requests.Session, timeout: float) -> str:
    response = session.get(
        f"{BASE_URL}/titles",
        params={"q": query},
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    logger.debug(
        "GET %s -> %s %s (%d bytes)",
        response.url,
        response.status_code,
        response.reason,
        len(response.content),
    )
    response.raise_for_status()
    return response.text


def _fetch_detail_page_html(url: str, session: requests.Session, timeout: float) -> str:
    response = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    logger.debug(
        "GET %s -> %s %s (%d bytes)",
        response.url,
        response.status_code,
        response.reason,
        len(response.content),
    )
    response.raise_for_status()
    return response.text


def _parse_search_results(html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.select('a[href^="/titles/"]')
    results = []
    for anchor in anchors:
        img = anchor.find("img", attrs={"data-testid": "grid-image"})
        if img is None:
            continue
        title = img.get("alt")
        if not title:
            continue
        url = urljoin(BASE_URL, anchor["href"])
        results.append((url, title))
    logger.debug(
        "_parse_search_results(): %d '/titles/' link(s) on page, %d matched the grid-image filter",
        len(anchors),
        len(results),
    )
    return results


def parse_detail_page(html: str, url: str) -> BookMetadata:
    soup = BeautifulSoup(html, "html.parser")
    ld = _find_audiobook_jsonld(soup)

    title = ld.get("name") if ld else None
    title_header = soup.find(attrs={"data-testid": "title-header"})
    if not title:
        title = title_header.get_text(strip=True) if title_header else None
    if not title:
        raise ValueError(f"Could not determine title for {url}")

    return BookMetadata(
        title=title,
        author=_parse_author(ld),
        narrator=_text_after_prefix(soup, "label-performed-by", "Performed by "),
        publisher=(ld.get("publisher") or {}).get("name") if ld else None,
        published_year=_parse_published_year(ld, soup),
        description=_parse_description(ld, soup),
        cover=ld.get("image") if ld else None,
        genres=list(ld.get("genre") or []) if ld else [],
        series=_parse_series_field(soup),
        language=_text_after_prefix(soup, "label-language", "Language: "),
        duration=_parse_duration_field(soup),
    )


def _find_audiobook_jsonld(soup: BeautifulSoup) -> dict | None:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        if data.get("@type") == "Audiobook":
            return data
    logger.warning(
        "No 'Audiobook' JSON-LD block found on detail page - Podium's page structure may "
        "have changed; title/author/cover/etc. will fall back to data-testid scraping only"
    )
    return None


def _parse_author(ld: dict | None) -> str | None:
    if not ld:
        return None
    names = (ld.get("author") or {}).get("name")
    if not names:
        return None
    if isinstance(names, str):
        return names
    return ", ".join(names)


def _parse_published_year(ld: dict | None, soup: BeautifulSoup) -> str | None:
    date_text = ld.get("datePublished") if ld else None
    if not date_text:
        date_text = _text_after_prefix(soup, "label-release-date", "Release Date: ")
    if not date_text:
        return None
    try:
        return str(datetime.strptime(date_text, "%B %d, %Y").year)
    except ValueError:
        return None


def _parse_description(ld: dict | None, soup: BeautifulSoup) -> str | None:
    element = soup.find(attrs={"data-testid": "description-section"})
    if element is not None:
        text = element.get_text(" ", strip=True)
        if text:
            return text
    if ld and ld.get("description"):
        return BeautifulSoup(ld["description"], "html.parser").get_text(" ", strip=True)
    return None


def _parse_series_field(soup: BeautifulSoup) -> list[SeriesMetadata]:
    element = soup.find(attrs={"data-testid": "title-series"})
    if element is None:
        return []
    text = element.get_text(strip=True)
    if not text:
        return []
    match = _SERIES_RE.match(text)
    if match:
        return [SeriesMetadata(series=match.group(1), sequence=match.group(2))]
    return [SeriesMetadata(series=text)]


def _parse_duration_field(soup: BeautifulSoup) -> int | None:
    text = _text_after_prefix(soup, "label-duration", "Duration: ")
    if not text:
        return None
    return _parse_duration_to_minutes(text)


def _parse_duration_to_minutes(text: str) -> int | None:
    hours_match = _HOURS_RE.search(text)
    minutes_match = _MINUTES_RE.search(text)
    if not hours_match and not minutes_match:
        return None
    hours = int(hours_match.group(1)) if hours_match else 0
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    return hours * 60 + minutes


def _text_after_prefix(soup: BeautifulSoup, testid: str, prefix: str) -> str | None:
    element = soup.find(attrs={"data-testid": testid})
    if element is None:
        return None
    text = element.get_text(" ", strip=True)
    if text.startswith(prefix):
        text = text[len(prefix):]
    return text or None
