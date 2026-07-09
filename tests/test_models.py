from abs_metadata_podium.models import BookMetadata, SeriesMetadata


def test_title_only_omits_everything_else():
    book = BookMetadata(title="Shadow of Mars")
    assert book.to_dict() == {"title": "Shadow of Mars"}


def test_full_book_matches_spec_field_names():
    book = BookMetadata(
        title="Shadow of Mars",
        author="Glynn Stewart",
        narrator="Jeffrey Kafer",
        publisher="Podium Entertainment",
        published_year="2026",
        description="The fleets of Mars have been forced into retreat.",
        cover="https://assets.podiumentertainment.com/medium/direct_cover_art/9798347007936.jpg",
        genres=["Sci-Fi"],
        series=[SeriesMetadata(series="Starship's Mage", sequence="18")],
        language="English",
        duration=723,
    )
    assert book.to_dict() == {
        "title": "Shadow of Mars",
        "author": "Glynn Stewart",
        "narrator": "Jeffrey Kafer",
        "publisher": "Podium Entertainment",
        "publishedYear": "2026",
        "description": "The fleets of Mars have been forced into retreat.",
        "cover": "https://assets.podiumentertainment.com/medium/direct_cover_art/9798347007936.jpg",
        "genres": ["Sci-Fi"],
        "series": [{"series": "Starship's Mage", "sequence": "18"}],
        "language": "English",
        "duration": 723,
    }


def test_series_without_sequence_omits_sequence_key():
    series = SeriesMetadata(series="Starship's Mage")
    assert series.to_dict() == {"series": "Starship's Mage"}


def test_multiple_authors_are_passed_through_as_single_joined_string():
    book = BookMetadata(title="He Who Fights with Monsters 5", author="Travis Deverell, Shirtaloon")
    assert book.to_dict()["author"] == "Travis Deverell, Shirtaloon"
