import pytest

from abs_metadata_podium import podium
from abs_metadata_podium.app import create_app
from abs_metadata_podium.config import Config
from abs_metadata_podium.models import BookMetadata


@pytest.fixture
def canned_book():
    return BookMetadata(title="Shadow of Mars", author="Glynn Stewart")


@pytest.fixture
def client_with_token(monkeypatch, canned_book):
    monkeypatch.setattr(podium, "search", lambda query, author=None: [canned_book])
    app = create_app(Config(auth_token="test-token"))
    return app.test_client()


@pytest.fixture
def client_without_token(monkeypatch, canned_book):
    monkeypatch.setattr(podium, "search", lambda query, author=None: [canned_book])
    app = create_app(Config(auth_token=None))
    return app.test_client()


def test_missing_query_returns_400(client_with_token):
    response = client_with_token.get("/search", headers={"AUTHORIZATION": "test-token"})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_missing_auth_header_returns_401(client_with_token):
    response = client_with_token.get("/search?query=Shadow+of+Mars")
    assert response.status_code == 401
    assert "error" in response.get_json()


def test_wrong_auth_header_returns_401(client_with_token):
    response = client_with_token.get(
        "/search?query=Shadow+of+Mars", headers={"AUTHORIZATION": "wrong-token"}
    )
    assert response.status_code == 401


def test_happy_path_returns_spec_shaped_matches(client_with_token):
    response = client_with_token.get(
        "/search?query=Shadow+of+Mars", headers={"AUTHORIZATION": "test-token"}
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "matches": [{"title": "Shadow of Mars", "author": "Glynn Stewart"}]
    }


def test_no_token_configured_skips_auth_check(client_without_token):
    response = client_without_token.get("/search?query=Shadow+of+Mars")
    assert response.status_code == 200


def test_search_failure_returns_500(monkeypatch):
    monkeypatch.setattr(podium, "search", lambda query, author=None: (_ for _ in ()).throw(RuntimeError("boom")))
    app = create_app(Config(auth_token=None))
    client = app.test_client()
    response = client.get("/search?query=Shadow+of+Mars")
    assert response.status_code == 500
    assert "error" in response.get_json()
