import json
from pathlib import Path
import wave
import pytest
from shortmaker import tts
from shortmaker.ffmpeg_runner import Cancelled
from shortmaker.models import Voiceover
from shortmaker.validation import parse_plan


def mock_models(tmp_path, monkeypatch, package=True):
    monkeypatch.setenv("SHORTMAKER_PIPER_MODELS", str(tmp_path))
    monkeypatch.setattr(tts.importlib.util, "find_spec", lambda _: object() if package else None)
    for voice_id in ("pt_BR-faber-medium", "pt_BR-cadu-medium"):
        (tmp_path / (voice_id + ".onnx")).touch()
        (tmp_path / (voice_id + ".onnx.json")).write_text("{}")


class FakeRunner:
    def __init__(self, failure=None):
        self.calls = []
        self.failure = failure

    def check(self):
        pass

    def run(self, args, **kwargs):
        request, output = Path(args[-2]), Path(args[-1])
        data = json.loads(request.read_text(encoding="utf-8"))
        self.calls.append(data)
        if data["engine"] == "piper" and self.failure:
            raise self.failure
        with wave.open(str(output), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(22050)
            wav.writeframes(b"\x01\x00" * 22050)


@pytest.mark.parametrize("voice_id", ["pt_BR-faber-medium", "pt_BR-cadu-medium"])
def test_piper_selection_and_voice_id(tmp_path, monkeypatch, voice_id):
    mock_models(tmp_path, monkeypatch)
    voice = Voiceover(enabled=True, engine="piper", voice_id=voice_id, text=tts.BENCHMARK)
    assert tts.select_engine(voice) == ("piper", None)
    runner = FakeRunner()
    output = tmp_path / "test.wav"
    assert tts.synthesize(voice, output, runner) == 1
    assert runner.calls[0]["voice_id"] == voice_id
    assert json.loads(output.with_suffix(".tts.result.json").read_text())["effective_engine"] == "piper"


def test_explicit_sapi_does_not_require_piper(tmp_path, monkeypatch):
    mock_models(tmp_path, monkeypatch, package=False)
    assert tts.select_engine(Voiceover(engine="sapi", voice="Maria")) == ("sapi", None)


@pytest.mark.parametrize("missing", ["package", "model", "config"])
def test_piper_unavailable_falls_back_to_sapi(tmp_path, monkeypatch, missing):
    mock_models(tmp_path, monkeypatch, package=missing != "package")
    if missing != "package":
        (tmp_path / ("pt_BR-faber-medium.onnx" + (".json" if missing == "config" else ""))).unlink()
    voice = Voiceover(enabled=True, engine="piper", text=tts.BENCHMARK, voice="Maria")
    runner = FakeRunner()
    output = tmp_path / "test.wav"
    assert tts.synthesize(voice, output, runner) == 1
    assert [c["engine"] for c in runner.calls] == ["sapi"]
    assert runner.calls[0]["voice"] == "Maria"
    result = json.loads(output.with_suffix(".tts.result.json").read_text(encoding="utf-8"))
    assert result["effective_engine"] == "sapi" and result["fallback_reason"]
    with pytest.raises(ValueError, match="amostras Piper não usam fallback"):
        tts.synthesize(voice, tmp_path / "strict.wav", FakeRunner(), allow_fallback=False)


def test_piper_load_failure_falls_back(tmp_path, monkeypatch):
    mock_models(tmp_path, monkeypatch)
    runner = FakeRunner(ValueError("model corrupt"))
    voice = Voiceover(enabled=True, engine="piper", text=tts.BENCHMARK)
    tts.synthesize(voice, tmp_path / "test.wav", runner)
    assert [c["engine"] for c in runner.calls] == ["piper", "sapi"]


def test_cancel_does_not_trigger_fallback(tmp_path, monkeypatch):
    mock_models(tmp_path, monkeypatch)
    runner = FakeRunner(Cancelled())
    with pytest.raises(Cancelled):
        tts.synthesize(Voiceover(enabled=True, engine="piper", text=tts.BENCHMARK), tmp_path / "test.wav", runner)
    assert [c["engine"] for c in runner.calls] == ["piper"]


def test_default_piper_and_short_segment_overrides():
    data = {"schema_version": "1.1", "shorts": [{"id": "one", "timeline": [{"type": "source_clip", "start": 0, "end": 10, "voiceover": {"enabled": True, "text": tts.BENCHMARK}}]}]}
    assert parse_plan(data).shorts[0].timeline[0].voiceover.engine == "piper"
    data["defaults"] = {"voice": {"engine": "piper", "voice_id": "pt_BR-faber-medium"}}
    data["shorts"][0]["voice"] = {"voice_id": "pt_BR-cadu-medium"}
    assert parse_plan(data).shorts[0].timeline[0].voiceover.voice_id == "pt_BR-cadu-medium"
    data["shorts"][0]["timeline"][0]["voiceover"]["engine"] = "sapi"
    assert parse_plan(data).shorts[0].timeline[0].voiceover.engine == "sapi"


def test_unknown_engine_and_path_traversal_rejected():
    with pytest.raises(ValueError, match="Engine não suportada"):
        tts.select_engine(Voiceover(engine="cloud"))
    with pytest.raises(ValueError, match="voice_id"):
        tts.model_paths("../../secret")


@pytest.mark.parametrize("voice_id", ["pt_BR-faber-medium", "pt_BR-cadu-medium"])
def test_real_piper_benchmark_is_local_audible_and_measured(tmp_path, voice_id):
    import array
    from shortmaker.ffmpeg_runner import Runner
    voice = Voiceover(enabled=True, engine="piper", voice_id=voice_id, text=tts.BENCHMARK)
    output = tmp_path / (voice_id + ".wav")
    duration = tts.synthesize(voice, output, Runner(), allow_fallback=False)
    with wave.open(str(output), "rb") as wav:
        assert (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) == (22050, 1, 2)
        assert wav.getnframes() / wav.getframerate() == duration
        samples = array.array("h", wav.readframes(wav.getnframes()))
    assert 2 < duration < 15
    assert max(abs(sample) for sample in samples) > 1000
    result = json.loads(output.with_suffix(".tts.result.json").read_text())
    assert result["effective_engine"] == "piper" and result["fallback_reason"] is None


def test_real_piper_montage_preserves_ducking_order_and_audio(tmp_path, monkeypatch):
    # Reuse the unchanged M3 audio/frame harness with real Piper in place of SAPI.
    import test_runtime
    monkeypatch.setattr(test_runtime, "Voiceover", lambda **kwargs: Voiceover(engine="piper", voice_id="pt_BR-faber-medium", **kwargs))
    test_runtime.test_real_sapi_montage_ducking_frames_and_failure(tmp_path)


def test_real_missing_model_uses_sapi(tmp_path, monkeypatch):
    from shortmaker.ffmpeg_runner import Runner
    monkeypatch.setenv("SHORTMAKER_PIPER_MODELS", str(tmp_path / "missing"))
    voice = Voiceover(enabled=True, engine="piper", text="Fallback local funcionando.")
    output = tmp_path / "fallback.wav"
    assert tts.synthesize(voice, output, Runner()) > .3
    result = json.loads(output.with_suffix(".tts.result.json").read_text(encoding="utf-8"))
    assert result["effective_engine"] == "sapi" and "indisponível" in result["fallback_reason"]


def test_real_piper_rate_and_volume_controls(tmp_path):
    import array
    from shortmaker.ffmpeg_runner import Runner
    slow = Voiceover(enabled=True, engine="piper", text=tts.BENCHMARK)
    normal_duration = tts.synthesize(slow, tmp_path / "normal.wav", Runner(), allow_fallback=False)
    fast = slow.model_copy(update={"rate": 2, "volume": 0})
    fast_duration = tts.synthesize(fast, tmp_path / "fast-silent.wav", Runner(), allow_fallback=False)
    assert fast_duration < normal_duration * .8
    with wave.open(str(tmp_path / "fast-silent.wav"), "rb") as wav:
        values = array.array("h", wav.readframes(wav.getnframes()))
    assert max(abs(value) for value in values) == 0
