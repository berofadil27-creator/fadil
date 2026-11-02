from app.detectors import text_detector
from app.services import text_model_service as tms

T = "Texte de test. " * 30


def _fake(level, status="ok"):
    return lambda text: tms.TextModelReport(status=status, level=level, score=None)


def test_unconfigured_is_honest(monkeypatch):
    monkeypatch.delenv("VEYRA_TEXT_DETECTOR_URL", raising=False)
    out = text_detector.analyze(T)
    assert out.conclusion == "inconclusive" and not out.detection_available
    assert out.indicators[0].status == "not_performed"


def test_high_gives_likely_ai(monkeypatch):
    monkeypatch.setattr(tms, "analyze", _fake("high"))
    out = text_detector.analyze(T)
    assert out.conclusion == "likely_ai" and out.detection_available
    assert out.indicators[0].status == "found"


def test_low_never_likely_human(monkeypatch):
    monkeypatch.setattr(tms, "analyze", _fake("low"))
    out = text_detector.analyze(T)
    assert out.conclusion == "inconclusive"
    assert out.indicators[0].status == "not_found"
    assert "ne prouve pas" in out.indicators[0].explanation


def test_uncertain(monkeypatch):
    monkeypatch.setattr(tms, "analyze", _fake("uncertain"))
    assert text_detector.analyze(T).conclusion == "inconclusive"


def test_error_is_not_performed(monkeypatch):
    monkeypatch.setattr(tms, "analyze", _fake(None, status="error"))
    out = text_detector.analyze(T)
    assert out.conclusion == "inconclusive" and not out.detection_available
    assert out.indicators[0].status == "not_performed"


def test_levels(monkeypatch):
    class R:
        status_code = 200
        def __init__(self, s): self.s = s
        def json(self): return {"score": self.s}
    monkeypatch.setenv("VEYRA_TEXT_DETECTOR_URL", "https://x.hf.space")
    monkeypatch.setenv("VEYRA_DETECTOR_KEY", "k")
    for s, lvl in [(0.95, "high"), (0.5, "uncertain"), (0.05, "low")]:
        monkeypatch.setattr(tms.httpx, "post", lambda *a, s=s, **k: R(s))
        assert tms.analyze(T).level == lvl
