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
