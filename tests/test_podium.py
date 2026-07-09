from pathlib import Path

import pytest

from abs_metadata_podium import podium

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_search_results_filters_out_unrelated_carousel_links():
    html = load_fixture("search_shadow_of_mars.html")
    results = podium._parse_search_results(html)
    titles = {title for _url, title in results}
    assert titles == {"Shadow of Mars", "Ambassador for Mars"}


def test_parse_search_results_second_query_filters_out_carousel_links():
    html = load_fixture("search_he_who_fights_with_monsters_5.html")
    results = podium._parse_search_results(html)
    titles = {title for _url, title in results}
    assert titles == {"He Who Fights with Monsters 5: A LitRPG Adventure", "Rogue Ascension 5"}


def test_parse_detail_page_shadow_of_mars():
    html = load_fixture("detail_shadow_of_mars.html")
    book = podium.parse_detail_page(html, "https://podiumentertainment.com/titles/108350/shadow-of-mars")

    assert book.title == "Shadow of Mars"
    assert book.author == "Glynn Stewart"
    assert book.narrator == "Jeffrey Kafer"
    assert book.publisher == "Podium Entertainment"
    assert book.published_year == "2026"
    assert book.genres == ["Sci-Fi"]
    assert book.language == "English"
    assert book.duration == 723
    assert book.series == [podium.SeriesMetadata(series="Starship's Mage", sequence="18")]
    assert book.cover == "https://assets.podiumentertainment.com/medium/direct_cover_art/9798347007936.jpg"
    assert book.description


def test_parse_detail_page_handles_multiple_authors():
    html = load_fixture("detail_he_who_fights_with_monsters_5.html")
    book = podium.parse_detail_page(
        html,
        "https://podiumentertainment.com/titles/4569/he-who-fights-with-monsters-5-a-litrpg-adventure",
    )

    assert book.title == "He Who Fights with Monsters 5: A LitRPG Adventure"
    assert book.author == "Travis Deverell, Shirtaloon"
    assert book.narrator == "Heath Miller"
    assert book.published_year == "2022"
    assert book.genres == ["LitRPG & Gamelit"]
    assert book.duration == 20 * 60 + 5
    assert book.series == [podium.SeriesMetadata(series="He Who Fights with Monsters", sequence="5")]


@pytest.mark.parametrize(
    "text, expected_minutes",
    [
        ("12 hr, 3 min", 723),
        ("20 hr, 5 min", 1205),
        ("5 hr", 300),
        ("45 min", 45),
        ("1 hr", 60),
        ("no duration info", None),
    ],
)
def test_parse_duration_to_minutes(text, expected_minutes):
    assert podium._parse_duration_to_minutes(text) == expected_minutes


@pytest.mark.parametrize(
    "text, expected_series, expected_sequence",
    [
        ("Starship's Mage, Book 18", "Starship's Mage", "18"),
        ("He Who Fights with Monsters, Book 5", "He Who Fights with Monsters", "5"),
        ("Some Standalone Title", "Some Standalone Title", None),
        ("Starship's Mage, Book 2, 15", "Starship's Mage", "2, 15"),
    ],
)
def test_parse_series_field_via_full_html_snippet(text, expected_series, expected_sequence):
    from bs4 import BeautifulSoup

    html = f'<a data-testid="title-series">{text}</a>'
    soup = BeautifulSoup(html, "html.parser")
    result = podium._parse_series_field(soup)
    assert result == [podium.SeriesMetadata(series=expected_series, sequence=expected_sequence)]


def test_search_orchestration_uses_fetch_functions(monkeypatch):
    search_html = load_fixture("search_shadow_of_mars.html")
    detail_html = load_fixture("detail_shadow_of_mars.html")

    monkeypatch.setattr(podium, "_fetch_search_page_html", lambda *a, **k: search_html)
    monkeypatch.setattr(podium, "_fetch_detail_page_html", lambda *a, **k: detail_html)

    results = podium.search("Shadow of Mars")

    assert len(results) == 2
    assert {b.title for b in results} == {"Shadow of Mars"}


def test_search_does_not_append_author_to_the_podium_query(monkeypatch):
    search_html = load_fixture("search_shadow_of_mars.html")
    detail_html = load_fixture("detail_shadow_of_mars.html")
    captured_queries = []

    def fake_fetch_search_page_html(query, session, timeout):
        captured_queries.append(query)
        return search_html

    monkeypatch.setattr(podium, "_fetch_search_page_html", fake_fetch_search_page_html)
    monkeypatch.setattr(podium, "_fetch_detail_page_html", lambda *a, **k: detail_html)

    podium.search("Shadow of Mars", author="Glynn Stewart")

    assert captured_queries == ["Shadow of Mars"]
