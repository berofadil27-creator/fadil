import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin

from app.main import app
from app.services import rate_limit, store

client = TestClient(app)
H = {"X-Client-Id": "client-image-0001"}
FX = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def clean():
    store.clear(); rate_limit.reset()


def _post(data: bytes, name="x.jpg"):
    r = client.post("/api/analyze/image", files={"file": (name, data)}, headers=H)
    assert r.status_code == 200, r.text
    return r.json()


def _ind(d, name):
    return next(i for i in d["indicators"] if i["name"] == name)


def _png(info=None) -> bytes:
    b = io.BytesIO()
    Image.new("RGB", (32, 32), (10, 200, 30)).save(b, "PNG", pnginfo=info)
    return b.getvalue()


def _jpeg_with_camera() -> bytes:
    img = Image.new("RGB", (32, 32), (200, 10, 30))
    exif = Image.Exif()
    exif[0x010F] = "Canon"; exif[0x0110] = "Canon EOS R6"
    b = io.BytesIO(); img.save(b, "JPEG", exif=exif)
    return b.getvalue()


def test_plain_image_is_inconclusive():
    d = _post(_png(), "x.png")
    assert d["conclusion"] == "inconclusive"
    assert d["detection_available"] is True
    assert _ind(d, "metadata")["status"] == "not_found"
    assert _ind(d, "content_provenance")["status"] == "not_found"
    assert _ind(d, "visual_traces")["status"] == "not_performed"
    assert d["confidence"] is None


def test_stable_diffusion_parameters_png():
    info = PngImagePlugin.PngInfo()
    info.add_text("parameters", "a cat, Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 1")
    d = _post(_png(info), "x.png")
    assert d["conclusion"] == "likely_ai"
    assert "paramètres de génération" in _ind(d, "metadata")["explanation"]


def test_ai_tool_in_software_tag():
    info = PngImagePlugin.PngInfo(); info.add_text("Software", "Adobe Firefly")
    assert _post(_png(info), "x.png")["conclusion"] == "likely_ai"


def test_camera_exif_alone_is_not_proof():
    d = _post(_jpeg_with_camera())
    assert d["conclusion"] == "inconclusive"
    assert "Canon EOS R6" in _ind(d, "metadata")["explanation"]


def test_c2pa_ai_declared():
    d = _post((FX / "ai_c2pa.jpg").read_bytes())
    assert d["conclusion"] == "likely_ai"
    exp = _ind(d, "content_provenance")["explanation"]
    assert "IA générative" in exp and "non vérifié" in exp


def test_c2pa_camera_untrusted_issuer_stays_inconclusive():
    d = _post((FX / "cam_c2pa.jpg").read_bytes())
    assert d["conclusion"] == "inconclusive"
    assert "appareil photo" in _ind(d, "content_provenance")["explanation"]


def test_c2pa_tampered_is_ignored():
    d = _post((FX / "tampered.jpg").read_bytes())
    assert d["conclusion"] == "inconclusive"
    assert "échoue" in _ind(d, "content_provenance")["explanation"]


def test_c2pa_algorithmic_not_generative():
    d = _post((FX / "C.jpg").read_bytes())
    assert d["conclusion"] == "inconclusive"
    assert _ind(d, "content_provenance")["status"] == "found"


def test_remote_manifest_not_fetched():
    d = _post((FX / "cloud.jpg").read_bytes())
    assert "pas été vérifiées" in _ind(d, "content_provenance")["explanation"]
    assert d["conclusion"] == "inconclusive"


# --- Modèle visuel (simulé : aucun appel réseau dans les tests) ---
from app.services import visual_model_service as vms


def _fake(monkeypatch, report):
    monkeypatch.setattr(vms, "analyze", lambda data, filename="image": report)


def test_model_high_gives_likely_ai(monkeypatch):
    _fake(monkeypatch, vms.VisualReport(status="ok", level="high", score=0.97))
    d = _post(_png(), "x.png")
    assert d["conclusion"] == "likely_ai" and d["confidence"] is None
    assert "0.97" not in str(d)


def test_model_low_gives_likely_human(monkeypatch):
    _fake(monkeypatch, vms.VisualReport(status="ok", level="low", score=0.02))
    assert _post(_png(), "x.png")["conclusion"] == "likely_human"


def test_model_uncertain_is_inconclusive(monkeypatch):
    _fake(monkeypatch, vms.VisualReport(status="ok", level="uncertain", score=0.5))
    assert _post(_png(), "x.png")["conclusion"] == "inconclusive"


def test_declared_ai_beats_model_low(monkeypatch):
    _fake(monkeypatch, vms.VisualReport(status="ok", level="low", score=0.02))
    d = _post((FX / "ai_c2pa.jpg").read_bytes())
    assert d["conclusion"] == "likely_ai"
    assert any("divergent" in l for l in d["limitations"])


def test_model_error_is_reported(monkeypatch):
    _fake(monkeypatch, vms.VisualReport(status="error"))
    d = _post(_png(), "x.png")
    assert d["conclusion"] == "inconclusive"
    assert "n'a pas répondu" in _ind(d, "visual_traces")["explanation"]


def test_unconfigured_is_not_performed(monkeypatch):
    monkeypatch.delenv("SIGHTENGINE_API_USER", raising=False)
    monkeypatch.delenv("SIGHTENGINE_API_SECRET", raising=False)
    d = _post(_png(), "x.png")
    assert _ind(d, "visual_traces")["status"] == "not_performed"
