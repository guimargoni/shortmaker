import json
from pathlib import Path
import pytest
from shortmaker.validation import parse_plan, deep_merge, editorial_warnings
from shortmaker.timecodes import seconds
from shortmaker.output_naming import output_path, safe_name
from shortmaker.timeline import segment_duration, validate_ranges
from shortmaker.media_probe import Media
from shortmaker.captions import narration_events
from shortmaker.ass_builder import AssBuilder

ROOT = Path(__file__).resolve().parents[1]


def base():
    return {"schema_version": "1.1", "shorts": [{"id": "one", "timeline": [{"type": "source_clip", "start": 0, "end": 5}]}]}


@pytest.mark.parametrize("example", ["minimal_transformative", "full_future"])
def test_examples(example):
    plan = parse_plan((ROOT / "examples" / f"{example}.example.json").read_text(encoding="utf-8"))
    assert len(plan.shorts[0].timeline) == 3
    assert plan.shorts[0].timeline[0].voiceover.enabled
    assert plan.publishing["approval_required"]


@pytest.mark.parametrize("value,expected", [(1.2, 1.2), ("00:01:02.125", 62.125), ("01:02", 62), ("99:59:59", 359999)])
def test_timecodes(value, expected):
    assert seconds(value) == expected


@pytest.mark.parametrize("value", [True, -1, float("nan"), float("inf"), "00:60:01", "abc", "1:2:3"])
def test_invalid_times(value):
    with pytest.raises(ValueError):
        seconds(value)


def test_exact_path():
    data = base()
    data["shorts"][0]["timeline"].append({"type": "source_clip", "start": 8, "end": 3})
    with pytest.raises(ValueError, match=r"shorts\[0\].timeline\[1\].end"):
        parse_plan(data)


def test_inheritance():
    data = base()
    data["defaults"] = {"voice": {"rate": 1.2}, "captions": {"style": {"font_size": 52}}, "video": {"reframe": {"zoom": 1.1}}}
    data["shorts"][0]["voice"] = {"rate": 1.3}
    data["shorts"][0]["timeline"][0]["voiceover"] = {"rate": 1.4}
    segment = parse_plan(data).shorts[0].timeline[0]
    assert segment.voiceover.rate == 1.4
    assert segment.reframe.zoom == 1.1
    assert segment.captions["style"]["font_size"] == 52
    assert segment.captions["style"]["font_family"] == "Arial"
    assert deep_merge({"a": [1]}, {"a": [2]}) == {"a": [2]}


def test_unknown_preserved():
    data = base()
    data["future"] = {"thing": True}
    assert parse_plan(data).model_dump()["future"] == {"thing": True}


def test_naming(tmp_path):
    short = parse_plan(base()).shorts[0]
    short.publishing = {"platforms": {"youtube": {"title": "Olá: / mundo?"}}}
    first = output_path(tmp_path, short, 1)
    assert first.name == "01-ola-mundo-one.mp4"
    first.touch()
    assert output_path(tmp_path, short, 1).name == "01-ola-mundo-one-2.mp4"
    assert safe_name("CON") == "short-con"
    short.export["filename_template"] = "../../{id}"
    assert output_path(tmp_path, short, 1).parent == tmp_path


def test_overflow_and_range():
    segment = parse_plan(base()).shorts[0].timeline[0]
    assert segment_duration(segment, 6.5) == (6.5, 1.5)
    with pytest.raises(ValueError, match="Aumente end"):
        segment_duration(segment, 6.51)
    segment.speed = 2
    assert segment_duration(segment) == (2.5, 0)
    with pytest.raises(ValueError, match=r"timeline\[0\].end"):
        validate_ranges(parse_plan(base()).shorts[0], Media(4, 30, True, 1280, 720), 0)


def test_captions_and_utf8(tmp_path):
    events = narration_events("Uma ação. Você entendeu? Essa é a conclusão.", 4, .15, 12, 2)
    assert events[0][0] == .15
    assert events[-1][1] == pytest.approx(4.15)
    assert all(len(t.splitlines()) <= 2 and all(len(line) <= 12 for line in t.splitlines()) for _, _, t in events)
    ass = AssBuilder()
    ass.add(events, "Narration", {})
    ass.write(tmp_path / "text.ass")
    assert "ação" in (tmp_path / "text.ass").read_text(encoding="utf-8")


def test_warning_nonblocking():
    plan = parse_plan(base())
    assert "não é uma avaliação oficial" in editorial_warnings(plan)[0]
    assert plan.shorts[0].enabled


def test_local_review_preserves_metadata(tmp_path):
    from shortmaker.review import mark_review
    video = tmp_path / "short.mp4"
    video.touch()
    sidecar = video.with_suffix(".metadata.json")
    sidecar.write_text(json.dumps({"project": {"id": "x"}, "short": {"publishing": {"platforms": {"youtube": {"enabled": False}}}}}), encoding="utf-8")
    mark_review(video, True)
    assert json.loads(sidecar.read_text())["short"]["publishing"]["approved"]
    mark_review(video, False)
    data = json.loads(sidecar.read_text())
    assert data["project"]["id"] == "x"
    assert data["short"]["publishing"]["approval_state"] == "rejected"
    assert not data["short"]["publishing"]["platforms"]["youtube"]["enabled"]
