"""
Run with: python3 -m pytest tests/
Uses Flask's built-in test client, so this doesn't need a running server.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_movies_list(client):
    res = client.get("/api/movies")
    assert res.status_code == 200
    titles = res.get_json()["titles"]
    assert "Inception" in titles


def test_recommend_valid(client):
    res = client.post("/api/recommend", json={"movie": "Inception"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["matched_title"] == "Inception"
    assert len(body["recommendations"]) == 6
    for rec in body["recommendations"]:
        assert rec["title"] != "Inception"  # never recommend the input back to itself


def test_recommend_fuzzy_typo(client):
    res = client.post("/api/recommend", json={"movie": "Incepton"})
    assert res.status_code == 200
    assert res.get_json()["matched_title"] == "Inception"


def test_recommend_empty_input(client):
    res = client.post("/api/recommend", json={"movie": ""})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_recommend_missing_field(client):
    res = client.post("/api/recommend", json={})
    assert res.status_code == 400


def test_recommend_malformed_json(client):
    res = client.post("/api/recommend", data="not json", content_type="application/json")
    assert res.status_code == 400


def test_recommend_unknown_movie(client):
    res = client.post("/api/recommend", json={"movie": "zzqxnotamovie999"})
    assert res.status_code == 404


def test_recommend_wrong_method(client):
    res = client.get("/api/recommend")
    assert res.status_code == 405


def test_unknown_route(client):
    res = client.get("/api/nope")
    assert res.status_code == 404
