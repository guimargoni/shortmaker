import json
import logging
from pathlib import Path
import pytest
from shortmaker.pronunciation import apply_overrides
from shortmaker.models import Reframe, Voiceover
from shortmaker.validation import parse_plan
from shortmaker.captions import narration_events
from shortmaker.tts import synthesize
from shortmaker.reframe import focus_faces, smooth_focus, crop_filter, analyze_anime


def test_pronunciation_whole_words_case_punctuation_multiple():
    text = "Eren, Eren! eren? EREN; Erenville. Mikasa e Armin."
    spoken, applied = apply_overrides(text, {"Eren": "Éren", "Mikasa": "Micássa", "Armin": "Ármin"})
    assert spoken == "Éren, Éren! Éren? Éren; Erenville. Micássa e Ármin."
    assert len(applied) == 6
    assert text.startswith("Eren,")


def test_case_sensitive_priority_and_no_recursive_substitution():
    assert apply_overrides("Eren eren EREN", {"Eren": "A", "eren": "B"})[0] == "A B A"
    assert apply_overrides("Eren", {"Eren": "Armin", "Armin": "Ármin"})[0] == "Armin"


def test_short_override_and_original_captions_metadata(tmp_path, caplog):
    from test_tts_engines import FakeRunner
    data = {"schema_version": "1.1", "defaults": {"voice": {"engine": "sapi", "pronunciation_overrides": {"Eren": "global", "Armin": "Ármin"}}}, "shorts": [{"id": "x", "voice": {"pronunciation_overrides": {"Eren": "Éren"}}, "timeline": [{"type": "source_clip", "start": 0, "end": 5, "voiceover": {"enabled": True, "text": "Eren e Armin."}}]}]}
    plan = parse_plan(data)
    voice = plan.shorts[0].timeline[0].voiceover
    assert voice.pronunciation_overrides == {"Eren": "Éren", "Armin": "Ármin"}
    runner = FakeRunner()
    with caplog.at_level(logging.INFO):
        synthesize(voice, tmp_path / "voice.wav", runner)
    assert runner.calls[0]["text"] == "Éren e Ármin."
    assert voice.text == "Eren e Armin."
    assert "Eren" in narration_events(voice.text, 1)[0][2]
    assert plan.model_dump()["shorts"][0]["timeline"][0]["voiceover"]["text"] == "Eren e Armin."
    assert "Pronunciation overrides aplicados" in caplog.text


def test_faces_largest_hysteresis_and_pair():
    assert focus_faces([], None, 1920, 1080) is None
    assert focus_faces([(100, 200, 100, 100), (1400, 200, 200, 200)], None, 1920, 1080)[0] > .7
    assert focus_faces([(100, 200, 180, 180), (1400, 200, 200, 200)], (.1, .25), 1920, 1080)[0] < .2
    paired = focus_faces([(750, 200, 100, 100), (900, 200, 100, 100)], None, 1920, 1080)
    assert paired[0] == pytest.approx(875/1920)


def test_smoothing_and_bounded_crop():
    target = (.6, .5)
    result = smooth_focus(target, (.5, .5), .3)
    assert .5 < result[0] < .6
    expression = crop_filter([(0, .1, .5), (4.5, .9, .4)])
    assert "clip((t-" in expression and "min(iw-1080" in expression


@pytest.mark.parametrize("frames", [[], [{"at": 1, "x": .5, "y": .5}, {"at": 0, "x": .5, "y": .5}], [{"at": 0, "x": 1.2, "y": .5}]])
def test_bad_manual_keyframes(frames):
    with pytest.raises(ValueError):
        Reframe(mode="manual_keyframes", keyframes=frames)


def test_missing_detector_fallback(tmp_path, monkeypatch):
    import shortmaker.reframe as reframe
    from shortmaker.models import Segment
    from shortmaker.ffmpeg_runner import Runner
    monkeypatch.setattr(reframe, "CASCADE", tmp_path / "missing.xml")
    points, stats = analyze_anime("unused", Segment(type="source_clip", start=0, end=2), tmp_path, 0, Runner(), "unused")
    assert points == [(0, .5, .5)] and stats["fallback"]


def test_manual_and_no_faces_render_real(tmp_path):
    from shortmaker.paths import executable
    from shortmaker.ffmpeg_runner import Runner
    from shortmaker.render_pipeline import Pipeline
    runner = Runner()
    source = tmp_path / "source.mp4"
    runner.run([executable("ffmpeg"), "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=15:duration=2", "-c:v", "libx264", "-preset", "ultrafast", source])
    data = {"schema_version": "1.1", "defaults": {"video": {"preset": "ultrafast"}}, "shorts": [
        {"id": "manual", "timeline": [{"type": "source_clip", "start": 0, "end": 2, "reframe": {"mode": "manual_keyframes", "keyframes": [{"at": 0, "x": .2, "y": .5}, {"at": 1.5, "x": .8, "y": .5}]}}]},
        {"id": "no-face", "timeline": [{"type": "source_clip", "start": 0, "end": 2, "reframe": {"mode": "anime_face_track"}}]}]}
    outputs, failures = Pipeline().render(source, parse_plan(data), tmp_path / "out")
    assert len(outputs) == 2 and not failures
    report = json.loads(outputs[1].with_suffix(".metadata.json").read_text(encoding="utf-8"))["reframe_report"][0]
    assert report["frames_with_faces"] == 0 and report["fallback"]
    info = json.loads(runner.run([executable("ffprobe"), "-v", "error", "-show_streams", "-of", "json", outputs[0]]))
    assert (info["streams"][0]["width"], info["streams"][0]["height"]) == (1080, 1920)
