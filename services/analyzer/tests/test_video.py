import pytest
from app.detectors import video_detector
from app.services import visual_model_service as vms

F = [b"x"] * 6
T = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setenv("SIGHTENGINE_API_USER", "u")
    monkeypatch.setenv("SIGHTENGINE_API_SECRET", "s")
    monkeypatch.setattr(vms, "take_quota", lambda n=1: True)


def _levels(monkeypatch, levels):
    it = iter(levels)
    monkeypatch.setattr(vms, "analyze", lambda d, f="i", reserved=False: (
        lambda l: vms.VisualReport(status="error") if l is None else vms.VisualReport(status="ok", level=l))(next(it)))


def test_mostly_high_is_likely_ai(monkeypatch):
    _levels(monkeypatch, ["high"] * 4 + ["uncertain", "low"])
    out = video_detector.analyze(F, T, 6.0)
    assert out.conclusion == "likely_ai"
    assert out.indicators[1].status == "found"  # divergence high/low
    assert "6 images" in out.indicators[0].explanation


def test_all_low_is_likely_human(monkeypatch):
    _levels(monkeypatch, ["low"] * 6)
    out = video_detector.analyze(F, T, 6.0)
    assert out.conclusion == "likely_human"
    assert any("deepfake" in l for l in out.limitations)


def test_mixed_is_inconclusive(monkeypatch):
    _levels(monkeypatch, ["high", "high", "low", "low", "uncertain", "uncertain"])
    assert video_detector.analyze(F, T, 6.0).conclusion == "inconclusive"


def test_errors_reduce_to_inconclusive(monkeypatch):
    _levels(monkeypatch, [None, None, None, None, "high", "high"])
    out = video_detector.analyze(F, T, 6.0)
    assert out.conclusion == "inconclusive"
    assert out.indicators[0].explanation.startswith("2 images")


def test_quota_refused(monkeypatch):
    monkeypatch.setattr(vms, "take_quota", lambda n=1: False)
    out = video_detector.analyze(F, T, 6.0)
    assert out.conclusion == "inconclusive" and not out.detection_available


def test_take_quota_all_or_nothing(monkeypatch):
    monkeypatch.undo()
    vms._day.update(date="", count=0)
    assert vms.take_quota(vms.DAILY_CAP - 2)
    assert not vms.take_quota(3)
    assert vms.take_quota(2)


# --- 8.5 : provenance C2PA lue par le navigateur ---
import json

P = video_detector.parse_client_provenance


def test_parse_rejects_garbage():
    assert P(None) is None and P("") is None and P("{bad") is None
    assert P(json.dumps({"status": "hacked"})) is None
    assert P("x" * 5000) is None


def test_parse_maps_source_types():
    p = P(json.dumps({"status": "valid", "issuer": "OpenAI", "generator": "Sora",
                      "source_types": ["trainedAlgorithmicMedia", 3, "unknown"]}))
    assert p.ai_declarations == ["créé par une IA générative"] and p.capture_declarations == []


def test_no_provenance_says_not_performed(monkeypatch):
    _levels(monkeypatch, ["low"] * 6)
    out = video_detector.analyze(F, T, 6.0)
    prov = [i for i in out.indicators if i.name == "content_provenance"][0]
    assert prov.status == "not_performed"


def test_absent_provenance_does_not_change_conclusion(monkeypatch):
    _levels(monkeypatch, ["low"] * 6)
    out = video_detector.analyze(F, T, 6.0, P(json.dumps({"status": "absent"})))
    prov = [i for i in out.indicators if i.name == "content_provenance"][0]
    assert prov.status == "not_found" and out.conclusion == "likely_human"
    assert "appareil" in prov.explanation


def test_signed_ai_declaration_is_likely_ai(monkeypatch):
    _levels(monkeypatch, ["low"] * 6)
    out = video_detector.analyze(F, T, 6.0, P(json.dumps({"status": "valid", "source_types": ["trainedAlgorithmicMedia"]})))
    assert out.conclusion == "likely_ai"
    assert any("divergent" in l for l in out.limitations)


def test_invalid_signature_ignored(monkeypatch):
    _levels(monkeypatch, ["low"] * 6)
    out = video_detector.analyze(F, T, 6.0, P(json.dumps({"status": "invalid", "source_types": ["trainedAlgorithmicMedia"]})))
    assert out.conclusion == "likely_human"


def test_capture_declaration_never_proves_human(monkeypatch):
    _levels(monkeypatch, ["high"] * 2 + ["uncertain"] * 4)
    out = video_detector.analyze(F, T, 6.0, P(json.dumps({"status": "trusted", "source_types": ["digitalCapture"]})))
    assert out.conclusion == "inconclusive"


def test_ai_declaration_when_quota_reached(monkeypatch):
    monkeypatch.setattr(vms, "take_quota", lambda n=1: False)
    out = video_detector.analyze(F, T, 6.0, P(json.dumps({"status": "valid", "source_types": ["trainedAlgorithmicMedia"]})))
    assert out.conclusion == "likely_ai" and out.detection_available


# --- 8.6 : indice d'IA dès la moitié des images ---
def _hint(out):
    return [i for i in out.indicators if i.name == "ai_hint"]


def test_half_high_gives_ai_hint(monkeypatch):
    _levels(monkeypatch, ["high"] * 3 + ["low"] * 3)
    out = video_detector.analyze(F, T, 14.0)
    assert out.conclusion == "inconclusive" and len(_hint(out)) == 1


def test_less_than_half_no_hint(monkeypatch):
    _levels(monkeypatch, ["high"] * 2 + ["low"] * 4)
    out = video_detector.analyze(F, T, 6.0)
    assert out.conclusion == "inconclusive" and not _hint(out)


def test_two_thirds_still_likely_ai_without_hint(monkeypatch):
    _levels(monkeypatch, ["high"] * 4 + ["low"] * 2)
    out = video_detector.analyze(F, T, 6.0)
    assert out.conclusion == "likely_ai" and not _hint(out)


def test_too_few_frames_no_hint(monkeypatch):
    _levels(monkeypatch, ["high", "low", None, None, None, None])
    out = video_detector.analyze(F, T, 6.0)
    assert not _hint(out)
