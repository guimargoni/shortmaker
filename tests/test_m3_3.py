import pytest
from shortmaker.ass_builder import AssBuilder, caption_text
from shortmaker.branding import add_end_tag
from shortmaker.settings import Captions, EndTag
from shortmaker.validation import parse_plan


def test_premium_highlight_whole_words_and_escaping():
    settings = Captions(style_preset="premium", highlight_keywords=True, keywords=["Eren", "muralhas"]).model_dump()
    text = caption_text("Eren, Erenville e muralhas. {\\pos(0,0)}", settings)
    assert text.count(r"{\1c&H004DD8FF&}") == 2
    assert "Erenville" in text and r"{\pos(0,0)}" not in text
    assert text.count(r"{\1c&H00FFFFFF&}") == 2


def test_old_captions_and_no_keywords_fallback():
    original = AssBuilder()
    original.add([(0, 1, "Eren está aqui.")], "Narration", {})
    assert original.events[0].endswith(",,Eren está aqui.")
    assert caption_text("Eren", {"style_preset": "premium", "highlight_keywords": True}) == "Eren"
    assert caption_text("Eren", {"keywords": ["Eren"], "highlight_keywords": True}) == "Eren"
    premium = AssBuilder()
    premium.add([(0, 1, "Eren")], "Narration", {"style_preset": "premium"})
    assert ",&H00FFFFFF," in premium.styles[0]


def test_end_tag_timing_fade_local_vector_and_disabled():
    ass = AssBuilder()
    add_end_tag(ass, 5, EndTag().model_dump())
    assert not ass.events
    add_end_tag(ass, 5, EndTag(enabled=True, text="Canal {\\pos(0,0)}").model_dump())
    assert len(ass.events) == 3
    assert all(",0:00:04.00,0:00:05.00," in event for event in ass.events)
    assert all(r"\fad(120,160)" in event for event in ass.events)
    assert r"\p1" in ass.events[-1]
    assert "Canal (＼pos(0,0))" in ass.events[0]


def test_branding_defaults_local_precedence():
    plan = parse_plan({"schema_version": "1.1", "defaults": {"branding": {"end_tag": {"enabled": True, "text": "Global"}}}, "shorts": [{"id": "x", "branding": {"end_tag": {"text": "Local"}}, "timeline": [{"type": "source_clip", "start": 0, "end": 1}]}]})
    assert plan.shorts[0].branding["end_tag"]["text"] == "Local"
    assert plan.shorts[0].branding["end_tag"]["enabled"]


@pytest.mark.parametrize("bad", [{"highlight_color": "red"}, {"keywords": ["a", "b", "c"]}])
def test_invalid_caption_settings(bad):
    with pytest.raises(ValueError):
        Captions(**bad)


def test_invalid_end_tag_duration():
    with pytest.raises(ValueError):
        EndTag(duration=4)
