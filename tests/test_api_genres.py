"""
Integration tests for genre API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def create_genre(client: TestClient, name: str, *, description: str | None = None, parent_id: int | None = None):
    """Helper to POST a genre and return the response."""
    data: dict = {"name": name}
    if description is not None:
        data["description"] = description
    if parent_id is not None:
        data["parent_id"] = str(parent_id)
    return client.post("/genres/", data=data)


class TestCreateGenre:
    def test_create_minimal(self, client: TestClient):
        response = create_genre(client, "Fantasy")

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Fantasy"
        assert data["slug"] == "fantasy"
        assert data["description"] is None
        assert data["parent_id"] is None
        assert "id" in data

    def test_create_with_description(self, client: TestClient):
        response = create_genre(client, "Horror", description="Dark and scary fiction")

        assert response.status_code == 201
        assert response.json()["description"] == "Dark and scary fiction"

    def test_create_with_parent(self, client: TestClient):
        parent_response = create_genre(client, "Fiction")
        parent_id = parent_response.json()["id"]

        response = create_genre(client, "Mystery", parent_id=parent_id)

        assert response.status_code == 201
        assert response.json()["parent_id"] == parent_id

    def test_create_slug_generated(self, client: TestClient):
        response = create_genre(client, "Science Fiction")

        assert response.status_code == 201
        assert response.json()["slug"] == "science-fiction"

    def test_create_slug_special_chars(self, client: TestClient):
        response = create_genre(client, "Children's")

        assert response.status_code == 201
        assert response.json()["slug"] == "children-s"

    def test_create_missing_name(self, client: TestClient):
        response = client.post("/genres/", data={})

        assert response.status_code == 422

    def test_create_empty_name(self, client: TestClient):
        response = client.post("/genres/", data={"name": ""})

        assert response.status_code == 422


class TestListGenres:
    def test_list_empty(self, client: TestClient):
        response = client.get("/genres/")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_all(self, client: TestClient):
        create_genre(client, "Fiction")
        create_genre(client, "Non-Fiction")
        create_genre(client, "Poetry")

        response = client.get("/genres/")

        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_list_item_structure(self, client: TestClient):
        create_genre(client, "Drama")

        response = client.get("/genres/")

        assert response.status_code == 200
        item = response.json()[0]
        assert "id" in item
        assert "name" in item
        assert "slug" in item
        assert "parent_id" in item

    def test_list_includes_children(self, client: TestClient):
        parent = create_genre(client, "Fiction").json()
        create_genre(client, "Sci-Fi", parent_id=parent["id"])

        response = client.get("/genres/")

        assert response.status_code == 200
        names = [g["name"] for g in response.json()]
        assert "Fiction" in names
        assert "Sci-Fi" in names


class TestGetGenreTree:
    def test_tree_empty(self, client: TestClient):
        response = client.get("/genres/tree")

        assert response.status_code == 200
        assert response.json() == []

    def test_tree_top_level_only(self, client: TestClient):
        create_genre(client, "Fiction")
        create_genre(client, "Non-Fiction")

        response = client.get("/genres/tree")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for node in data:
            assert node["children"] == []

    def test_tree_nests_children(self, client: TestClient):
        parent = create_genre(client, "Fiction").json()
        child = create_genre(client, "Mystery", parent_id=parent["id"]).json()

        response = client.get("/genres/tree")

        assert response.status_code == 200
        roots = response.json()
        assert len(roots) == 1
        assert roots[0]["id"] == parent["id"]
        assert len(roots[0]["children"]) == 1
        assert roots[0]["children"][0]["id"] == child["id"]

    def test_tree_deep_nesting(self, client: TestClient):
        grandparent = create_genre(client, "Fiction").json()
        parent = create_genre(client, "Science Fiction", parent_id=grandparent["id"]).json()
        grandchild = create_genre(client, "Space Opera", parent_id=parent["id"]).json()

        response = client.get("/genres/tree")

        assert response.status_code == 200
        roots = response.json()
        assert len(roots) == 1
        fiction_node = roots[0]
        assert len(fiction_node["children"]) == 1
        scifi_node = fiction_node["children"][0]
        assert scifi_node["id"] == parent["id"]
        assert len(scifi_node["children"]) == 1
        assert scifi_node["children"][0]["id"] == grandchild["id"]


class TestGetGenre:
    def test_get_by_id(self, client: TestClient):
        created = create_genre(client, "Thriller", description="Edge-of-your-seat fiction").json()
        genre_id = created["id"]

        response = client.get(f"/genres/{genre_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == genre_id
        assert data["name"] == "Thriller"
        assert data["slug"] == "thriller"
        assert data["description"] == "Edge-of-your-seat fiction"
        assert data["parent_id"] is None

    def test_get_not_found(self, client: TestClient):
        response = client.get("/genres/99999")

        assert response.status_code == 404

    def test_get_with_parent_id(self, client: TestClient):
        parent = create_genre(client, "Fiction").json()
        child = create_genre(client, "Romance", parent_id=parent["id"]).json()

        response = client.get(f"/genres/{child['id']}")

        assert response.status_code == 200
        assert response.json()["parent_id"] == parent["id"]


class TestListChildren:
    def test_list_children_empty(self, client: TestClient):
        parent = create_genre(client, "Fiction").json()

        response = client.get(f"/genres/{parent['id']}/children")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_children_direct_only(self, client: TestClient):
        parent = create_genre(client, "Fiction").json()
        create_genre(client, "Mystery", parent_id=parent["id"])
        create_genre(client, "Thriller", parent_id=parent["id"])

        response = client.get(f"/genres/{parent['id']}/children")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_children_excludes_grandchildren(self, client: TestClient):
        grandparent = create_genre(client, "Fiction").json()
        parent = create_genre(client, "Science Fiction", parent_id=grandparent["id"]).json()
        create_genre(client, "Space Opera", parent_id=parent["id"])

        response = client.get(f"/genres/{grandparent['id']}/children")

        assert response.status_code == 200
        children = response.json()
        assert len(children) == 1
        assert children[0]["id"] == parent["id"]
