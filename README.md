# abs-metadata-podium

An [Audiobookshelf](https://www.audiobookshelf.org/) custom metadata provider
that searches [Podium Entertainment](https://podiumentertainment.com/)'s
website for a title and scrapes metadata and cover art from the matching
book page. Implements the single `GET /search` endpoint described by
[audiobookshelf's custom-metadata-provider-specification](https://raw.githubusercontent.com/advplyr/audiobookshelf/refs/heads/master/custom-metadata-provider-specification.yaml).

This is an early beta: it works by scraping public HTML pages, so it may
break if Podium changes their site. It has no cache, database, or retry
logic — just a search followed by a bounded number of detail-page fetches.

## Install

```bash
pip install -e ".[dev]"
```

## Run

```bash
export ABS_METADATA_PODIUM_TOKEN=some-shared-secret
abs-metadata-podium
# or: python -m abs_metadata_podium
# or override host/port/token on the CLI:
abs-metadata-podium --host 127.0.0.1 --port 9000 --token some-shared-secret

# enable debug logging (logs the Podium URLs requested and the metadata parsed from each page):
abs-metadata-podium --debug
```

Environment variables:

| Variable                    | Default   | Purpose                                                                                      |
|-----------------------------|-----------|----------------------------------------------------------------------------------------------|
| `ABS_METADATA_PODIUM_TOKEN` | unset     | Shared secret expected in the `AUTHORIZATION` header. If unset, auth is disabled (dev-only). |
| `ABS_METADATA_PODIUM_HOST`  | `0.0.0.0` | Host to bind to.                                                                             |
| `ABS_METADATA_PODIUM_PORT`  | `8000`    | Port to bind to.                                                                             |
| `ABS_METADATA_PODIUM_DEBUG` | unset     | Set to `1`/`true`/`yes` to enable debug logging (same as `--debug`).                         |

### Debugging "no metadata found"

Run with `--debug` (or `ABS_METADATA_PODIUM_DEBUG=1`) and watch the logs while
Audiobookshelf performs a search. This logs: the incoming `query`/`author`
from ABS, every Podium URL requested (search page and each detail page) with
its HTTP status, how many search results were found vs. filtered out, and the
full metadata parsed from each detail page. This will show, for example,
whether ABS is sending an unexpected query, whether Podium is returning a
non-200 response, or whether Podium's page structure has changed and broken
the scraper.

## Configure in Audiobookshelf

In Audiobookshelf's metadata provider settings, add a custom provider
pointing at this server's base URL (e.g. `http://<host>:8000`) and set its
auth header value to match `ABS_METADATA_PODIUM_TOKEN`.

## Test

```bash
pytest
```

Tests run entirely offline against saved HTML fixtures in `tests/fixtures/`.

## Manual end-to-end check

```bash
curl -H "AUTHORIZATION: some-shared-secret" \
  "http://localhost:8000/search?query=Shadow%20of%20Mars"
```

## Docker

```bash
docker build -t abs-metadata-podium .
docker run -p 8000:8000 -e ABS_METADATA_PODIUM_TOKEN=some-shared-secret abs-metadata-podium
```
