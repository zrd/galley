"""
Integration tests for the public store API endpoints.
"""

import io
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import EbookModel


SAMPLE_EPUB = b"PK\x03\x04" + b"x" * 1000


def _register_public_author(client: TestClient, display_name: str = "Test Author") -> dict:
    """Register an author, make them public. Returns {headers, author_id}."""
    email = f"store-{uuid4()}@example.com"
    resp = client.post("/auth/register", json={
        "email": email, "password": "pw", "display_name": display_name,
    })
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    client.put("/authors/me", headers=headers, json={"is_public": True})
    author_id = client.get("/authors/me", headers=headers).json()["id"]
    return {"headers": headers, "author_id": author_id}


def _create_and_publish(client: TestClient, headers: dict, title: str = "My Book") -> dict:
    """Create a manuscript, mark ready, generate epub, publish. Returns {manuscript_id, ebook_id}."""
    resp = client.post(
        "/manuscripts/",
        headers=headers,
        data={"title": title, "source_format": "epub"},
        files={"file": ("book.epub", io.BytesIO(SAMPLE_EPUB), "application/epub+zip")},
    )
    manuscript_id = resp.json()["id"]
    client.post(f"/manuscripts/{manuscript_id}/ready", headers=headers)
    resp = client.post(
        f"/ebooks/manuscripts/{manuscript_id}/generate",
        headers=headers,
        json={"output_formats": ["epub"]},
    )
    ebook_id = resp.json()[0]["id"]
    client.post(f"/ebooks/{ebook_id}/publish", headers=headers)
    return {"manuscript_id": manuscript_id, "ebook_id": ebook_id}


@pytest.fixture
def author_setup(client: TestClient) -> dict:
    return _register_public_author(client)


@pytest.fixture
def listing(client: TestClient, author_setup: dict) -> dict:
    result = _create_and_publish(client, author_setup["headers"])
    return {**author_setup, **result}


class TestListEbooks:
    def test_returns_published_listings(self, client: TestClient, listing: dict):
        resp = client.get("/store/ebooks")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        item = data["items"][0]
        assert item["id"] == listing["manuscript_id"]
        assert len(item["editions"]) == 1

    def test_excludes_private_ebooks(self, client: TestClient, author_setup: dict):
        headers = author_setup["headers"]
        resp = client.post(
            "/manuscripts/",
            headers=headers,
            data={"title": "Draft Book", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(SAMPLE_EPUB), "application/epub+zip")},
        )
        manuscript_id = resp.json()["id"]
        client.post(f"/manuscripts/{manuscript_id}/ready", headers=headers)
        client.post(
            f"/ebooks/manuscripts/{manuscript_id}/generate",
            headers=headers,
            json={"output_formats": ["epub"]},
        )
        # ebook remains private (not published)
        resp = client.get("/store/ebooks")
        assert resp.json()["total"] == 0

    def test_filter_by_author_id(self, client: TestClient, listing: dict):
        other = _register_public_author(client, "Other Author")
        _create_and_publish(client, other["headers"], "Other Book")

        resp = client.get("/store/ebooks", params={"author_ids": listing["author_id"]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == listing["manuscript_id"]

    def test_filter_by_genre(self, client: TestClient, listing: dict):
        genre_resp = client.post("/genres/", data={"name": "Fiction"})
        genre_id = genre_resp.json()["id"]
        genre_slug = genre_resp.json()["slug"]
        client.put(
            f"/manuscripts/{listing['manuscript_id']}",
            headers=listing["headers"],
            json={"genre_ids": [genre_id]},
        )

        resp = client.get("/store/ebooks", params={"genre": genre_slug})
        assert resp.json()["total"] == 1

        resp = client.get("/store/ebooks", params={"genre": "nonexistent-genre"})
        assert resp.json()["total"] == 0

    def test_filter_by_tag(self, client: TestClient, listing: dict):
        client.put(
            f"/manuscripts/{listing['manuscript_id']}",
            headers=listing["headers"],
            json={"tag_names": ["fiction"]},
        )

        resp = client.get("/store/ebooks", params={"tag": "fiction"})
        assert resp.json()["total"] == 1

        resp = client.get("/store/ebooks", params={"tag": "nonfiction"})
        assert resp.json()["total"] == 0

    def test_filter_by_price(self, client: TestClient, listing: dict):
        client.patch(
            f"/ebooks/{listing['ebook_id']}",
            headers=listing["headers"],
            json={"list_price_cents": 999},
        )

        resp = client.get("/store/ebooks", params={"min_price": 500})
        assert resp.json()["total"] == 1

        resp = client.get("/store/ebooks", params={"max_price": 500})
        assert resp.json()["total"] == 0

    def test_search(self, client: TestClient, listing: dict):
        resp = client.get("/store/ebooks", params={"q": "My Book"})
        assert resp.json()["total"] == 1

        resp = client.get("/store/ebooks", params={"q": "Nonexistent Title XYZ"})
        assert resp.json()["total"] == 0

    def test_pagination(self, client: TestClient, author_setup: dict):
        headers = author_setup["headers"]
        for i in range(3):
            _create_and_publish(client, headers, f"Book {i}")

        resp = client.get("/store/ebooks", params={"page": 1, "per_page": 2})
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2

        resp = client.get("/store/ebooks", params={"page": 2, "per_page": 2})
        assert len(resp.json()["items"]) == 1


class TestLookupListing:
    def test_found(self, client: TestClient, listing: dict):
        resp = client.get(f"/store/ebooks/{listing['manuscript_id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == listing["manuscript_id"]
        assert len(data["editions"]) == 1

    def test_not_found(self, client: TestClient):
        resp = client.get(f"/store/ebooks/{uuid4()}")
        assert resp.status_code == 404

    def test_draft_manuscript_returns_404(self, client: TestClient, author_setup: dict):
        headers = author_setup["headers"]
        resp = client.post(
            "/manuscripts/",
            headers=headers,
            data={"title": "Draft", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(SAMPLE_EPUB), "application/epub+zip")},
        )
        manuscript_id = resp.json()["id"]

        resp = client.get(f"/store/ebooks/{manuscript_id}")
        assert resp.status_code == 404


class TestLookupEdition:
    def test_published_edition(self, client: TestClient, listing: dict):
        resp = client.get(f"/store/editions/{listing['ebook_id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == listing["ebook_id"]
        assert data["manuscript"]["id"] == listing["manuscript_id"]
        assert "download_url" in data

    def test_unlisted_edition(self, client: TestClient, listing: dict):
        client.post(f"/ebooks/{listing['ebook_id']}/unlist", headers=listing["headers"])
        resp = client.get(f"/store/editions/{listing['ebook_id']}")
        assert resp.status_code == 200

    def test_private_edition_returns_404(self, client: TestClient, listing: dict):
        client.post(f"/ebooks/{listing['ebook_id']}/make-private", headers=listing["headers"])
        resp = client.get(f"/store/editions/{listing['ebook_id']}")
        assert resp.status_code == 404

    def test_not_found(self, client: TestClient):
        resp = client.get(f"/store/editions/{uuid4()}")
        assert resp.status_code == 404

    def test_unlisted_limit_exceeded_returns_410(
        self, client: TestClient, db_session: Session, listing: dict
    ):
        client.post(f"/ebooks/{listing['ebook_id']}/unlist", headers=listing["headers"])

        ebook = db_session.get(EbookModel, UUID(listing["ebook_id"]))
        ebook.unlisted_download_limit = 1
        ebook.download_count = 1
        db_session.commit()

        resp = client.get(f"/store/editions/{listing['ebook_id']}")
        assert resp.status_code == 410


class TestBrowseAuthors:
    def test_returns_public_authors(self, client: TestClient, author_setup: dict):
        resp = client.get("/store/authors")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == author_setup["author_id"]

    def test_excludes_non_public_authors(self, client: TestClient):
        client.post("/auth/register", json={
            "email": f"private-{uuid4()}@example.com",
            "password": "pw",
            "display_name": "Private Author",
        })
        resp = client.get("/store/authors")
        assert resp.json()["total"] == 0

    def test_pagination(self, client: TestClient):
        for i in range(3):
            _register_public_author(client, f"Author {i}")

        resp = client.get("/store/authors", params={"page": 1, "per_page": 2})
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2


class TestLookupAuthor:
    def test_found(self, client: TestClient, author_setup: dict):
        resp = client.get(f"/store/authors/{author_setup['author_id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == author_setup["author_id"]
        assert "listings" in data

    def test_listings_populated(self, client: TestClient, listing: dict):
        resp = client.get(f"/store/authors/{listing['author_id']}")
        data = resp.json()
        assert len(data["listings"]) == 1
        assert data["listings"][0]["id"] == listing["manuscript_id"]

    def test_not_found(self, client: TestClient):
        resp = client.get(f"/store/authors/{uuid4()}")
        assert resp.status_code == 404

    def test_non_public_author_returns_404(self, client: TestClient):
        resp = client.post("/auth/register", json={
            "email": f"private-{uuid4()}@example.com",
            "password": "pw",
            "display_name": "Private Author",
        })
        headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
        author_id = client.get("/authors/me", headers=headers).json()["id"]

        resp = client.get(f"/store/authors/{author_id}")
        assert resp.status_code == 404


class TestBrowseGenres:
    def test_returns_genres_with_published_count(self, client: TestClient, listing: dict):
        genre_resp = client.post("/genres/", data={"name": "Fiction"})
        genre_id = genre_resp.json()["id"]
        client.put(
            f"/manuscripts/{listing['manuscript_id']}",
            headers=listing["headers"],
            json={"genre_ids": [genre_id]},
        )

        resp = client.get("/store/genres")
        assert resp.status_code == 200
        fiction = next(g for g in resp.json() if g["name"] == "Fiction")
        assert fiction["published_count"] == 1

    def test_count_excludes_private_ebooks(self, client: TestClient, author_setup: dict):
        headers = author_setup["headers"]
        genre_resp = client.post("/genres/", data={"name": "Mystery"})
        genre_id = genre_resp.json()["id"]

        resp = client.post(
            "/manuscripts/",
            headers=headers,
            data={"title": "Mystery Draft", "source_format": "epub"},
            files={"file": ("book.epub", io.BytesIO(SAMPLE_EPUB), "application/epub+zip")},
        )
        client.put(
            f"/manuscripts/{resp.json()['id']}",
            headers=headers,
            json={"genre_ids": [genre_id]},
        )

        resp = client.get("/store/genres")
        mystery = next(g for g in resp.json() if g["name"] == "Mystery")
        assert mystery["published_count"] == 0
