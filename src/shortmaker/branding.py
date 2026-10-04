"""Small local ASS end tag, without extending or interrupting audio/video."""
from .ass_builder import escape, stamp


def add_end_tag(ass, total, settings):
    if not settings.get("enabled"):
        return
    start = max(0, total - settings["duration"])
    # Compact reserved lower strip, below default captions; no opaque panel.
    ass.add([(start, total, settings["text"])], "EndTag", {"margin_bottom": 62}, 38)
    ass.events[-1] = ass.events[-1].replace(",," + escape(settings["text"]), r",,{\an2\pos(540,1838)\fad(120,160)}" + escape(settings["text"]))
    if settings.get("secondary_text"):
        ass.add([(start, total, settings["secondary_text"])], "EndSecondary", {"margin_bottom": 24}, 27)
        ass.events[-1] = ass.events[-1].replace(",," + escape(settings["secondary_text"]), r",,{\an2\pos(540,1882)\fad(120,160)}" + escape(settings["secondary_text"]))
    if settings.get("icon") == "thumbs_up":
        # Original simple vector silhouette (ASS drawing units); no external asset.
        drawing = r"{\an7\pos(295,1795)\fad(120,160)\bord1\shad0\p1}m 0 18 l 10 18 10 46 0 46 m 14 18 l 23 7 24 0 31 0 34 7 31 18 45 18 48 23 42 46 14 46{\p0}"
        ass.events.append(f"Dialogue: 1,{stamp(start)},{stamp(total)},EndTag,,0,0,0,,{drawing}")
