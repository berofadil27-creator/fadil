import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import rate_limit, store

client = TestClient(app)
H = {"X-Client-Id": "client-test-0001"}
OTHER = {"X-Client-Id": "client-test-0002"}
TEXT = "Ceci est un texte de test pour VEYRA. " * 12
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 100
MP4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 100


@pytest.fixture(autouse=True)
def clean():
    store.clear(); rate_limit.reset()


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_text_ok_is_honest():
    r = client.post("/api/analyze/text", json={"text": TEXT}, headers=H)
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "completed"
    assert d["conclusion"] == "inconclusive"
    assert d["confidence"] is None
    assert d["detection_available"] is False
    assert all(i["status"] == "not_performed" for i in d["indicators"])


def test_text_too_short():
    r = client.post("/api/analyze/text", json={"text": "trop court"}, headers=H)
    assert r.status_code == 422 and r.json()["error"]["code"] == "text_too_short"


def test_text_too_long():
    r = client.post("/api/analyze/text", json={"text": "a" * 20_001}, headers=H)
    assert r.status_code == 413


def test_missing_client_id():
    r = client.post("/api/analyze/text", json={"text": TEXT})
    assert r.status_code == 400 and r.json()["error"]["code"] == "missing_client_id"


def test_bad_body():
    r = client.post("/api/analyze/text", json={}, headers=H)
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"


@pytest.mark.parametrize("data", [PNG, JPEG])
def test_image_ok(data):
    r = client.post("/api/analyze/image", files={"file": ("x.png", data)}, headers=H)
    assert r.status_code == 200 and r.json()["content_type"] == "image"


def test_image_fake_extension_rejected():
    r = client.post("/api/analyze/image", files={"file": ("photo.jpg", b"not an image at all")}, headers=H)
    assert r.status_code == 415


def test_video_given_as_image_rejected():
    r = client.post("/api/analyze/image", files={"file": ("x.jpg", MP4)}, headers=H)
    assert r.status_code == 415


def test_video_ok():
    r = client.post("/api/analyze/video", files={"file": ("v.mp4", MP4)}, headers=H)
    assert r.status_code == 200 and len(r.json()["indicators"]) == 4


def test_empty_file():
    r = client.post("/api/analyze/image", files={"file": ("x.png", b"")}, headers=H)
    assert r.status_code == 422


def test_get_history_delete_and_rights():
    aid = client.post("/api/analyze/text", json={"text": TEXT}, headers=H).json()["analysis_id"]
    assert client.get(f"/api/analysis/{aid}", headers=H).status_code == 200
    assert client.get(f"/api/analysis/{aid}", headers=OTHER).status_code == 404
    assert len(client.get("/api/history", headers=H).json()["items"]) == 1
    assert client.get("/api/history", headers=OTHER).json()["items"] == []
    assert client.delete(f"/api/analysis/{aid}", headers=OTHER).status_code == 404
    assert client.delete(f"/api/analysis/{aid}", headers=H).status_code == 204
    assert client.get(f"/api/analysis/{aid}", headers=H).status_code == 404


def test_rate_limit():
    for _ in range(30):
        assert client.post("/api/analyze/text", json={"text": TEXT}, headers=H).status_code == 200
    r = client.post("/api/analyze/text", json={"text": TEXT}, headers=H)
    assert r.status_code == 429


def test_unknown_route():
    r = client.get("/api/nope")
    assert r.status_code == 404 and "error" in r.json()
