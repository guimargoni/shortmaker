from pathlib import Path
import re
import textwrap


def stamp(value):
    ticks = max(0, round(value * 100))
    return f"{ticks // 360000}:{ticks // 6000 % 60:02d}:{ticks // 100 % 60:02d}.{ticks % 100:02d}"


def escape(text):
    # User text cannot inject ASS override commands.
    return str(text).replace("\\", "＼").replace("{", "(").replace("}", ")").replace("\r", "").replace("\n", r"\N")


def color(value):
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError(f"Cor inválida: {value}; use #RRGGBB")
    return "&H00" + value[5:7] + value[3:5] + value[1:3]


def caption_text(text, settings):
    # Only generated color tags are trusted; all editorial text is escaped.
    if settings.get("style_preset") != "premium" or not settings.get("highlight_keywords"):
        return escape(text)
    keywords = [word for word in settings.get("keywords", []) if word.strip()]
    if not keywords:
        return escape(text)
    pattern = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(k) for k in sorted(keywords, key=len, reverse=True)) + r")(?!\w)", re.IGNORECASE)
    parts, cursor = [], 0
    for match in pattern.finditer(text):
        parts += [escape(text[cursor:match.start()]), r"{\1c" + color(settings.get("highlight_color", "#FFD84D")) + "&}", escape(match.group()), r"{\1c&H00FFFFFF&}"]
        cursor = match.end()
    return "".join(parts) + escape(text[cursor:])


class AssBuilder:
    def __init__(self):
        self.styles = []
        self.events = []

    def add(self, events, name, settings, default_size=64):
        style = dict(settings.get("style", {}))
        premium = name in {"Narration", "Dialogue"} and settings.get("style_preset") == "premium"
        if premium:
            style.update(font_color="#FFFFFF", outline_color="#000000", outline_width=3, font_weight="bold", background_enabled=False)
        position = settings.get("position", "bottom")
        alignment = {"top": 8, "center": 5, "bottom": 2}.get(position, 2)
        margin = settings.get("margin_top", 165) if position == "top" else settings.get("margin_bottom", 230)
        font = str(style.get("font_family", "Arial")).replace(",", "").replace("\n", "")
        size = float(style.get("font_size", default_size))
        outline = float(style.get("outline_width", 4))
        if not 8 <= size <= 200 or not 0 <= outline <= 20:
            raise ValueError("ASS: font_size deve ser 8–200 e outline_width 0–20")
        self.styles.append(f"Style: {name},{font},{size},{color(style.get('font_color', '#FFFFFF'))},&H000000FF,{color(style.get('outline_color', '#000000'))},&H80000000,{-1 if style.get('font_weight', 'bold') == 'bold' else 0},0,0,0,100,100,0,0,{3 if style.get('background_enabled') else 1},{outline},{1 if premium else 0},{alignment},60,60,{int(margin)},1")
        for start, end, text in events:
            if end > start:
                rendered = caption_text(text, settings) if premium else escape(text)
                self.events.append(f"Dialogue: 0,{stamp(start)},{stamp(end)},{name},,0,0,0,,{rendered}")

    def write(self, path):
        header = "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        Path(path).write_text(header + "\n".join(self.styles) + "\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" + "\n".join(self.events) + "\n", encoding="utf-8")


def wrap_overlay(text, width=30):
    return "\n".join(textwrap.wrap(str(text), width=width))
