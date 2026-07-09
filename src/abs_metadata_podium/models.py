from dataclasses import dataclass, field


@dataclass
class SeriesMetadata:
    series: str
    sequence: str | None = None

    def to_dict(self) -> dict:
        result = {"series": self.series}
        if self.sequence:
            result["sequence"] = self.sequence
        return result


@dataclass
class BookMetadata:
    title: str
    subtitle: str | None = None
    author: str | None = None
    narrator: str | None = None
    publisher: str | None = None
    published_year: str | None = None
    description: str | None = None
    cover: str | None = None
    isbn: str | None = None
    asin: str | None = None
    genres: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    series: list[SeriesMetadata] = field(default_factory=list)
    language: str | None = None
    duration: int | None = None

    def to_dict(self) -> dict:
        result = {"title": self.title}
        simple_fields = {
            "subtitle": self.subtitle,
            "author": self.author,
            "narrator": self.narrator,
            "publisher": self.publisher,
            "publishedYear": self.published_year,
            "description": self.description,
            "cover": self.cover,
            "isbn": self.isbn,
            "asin": self.asin,
            "language": self.language,
            "duration": self.duration,
        }
        for key, value in simple_fields.items():
            if value is not None:
                result[key] = value
        if self.genres:
            result["genres"] = self.genres
        if self.tags:
            result["tags"] = self.tags
        if self.series:
            result["series"] = [s.to_dict() for s in self.series]
        return result
