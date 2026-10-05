"""Validate renderer settings after inheritance while preserving future metadata."""
from typing import Literal
from pydantic import Field, field_validator
from .models import Model, SourceAudio, Reframe, Voiceover
from .editing_models import Editing


class Style(Model):
    font_family: str = "Arial"
    font_size: float = Field(default=64, ge=8, le=200)
    font_weight: str = "bold"
    font_color: str = Field(default="#FFFFFF", pattern=r"^#[0-9a-fA-F]{6}$")
    outline_color: str = Field(default="#000000", pattern=r"^#[0-9a-fA-F]{6}$")
    outline_width: float = Field(default=4, ge=0, le=20)
    background_enabled: bool = False


class Video(Model):
    width: Literal[1080] = 1080
    height: Literal[1920] = 1920
    aspect_ratio: Literal["9:16"] = "9:16"
    fps_mode: Literal["source", "fixed"] = "source"
    fps: float = Field(default=30, ge=1, le=120)
    video_codec: Literal["libx264"] = "libx264"
    pixel_format: Literal["yuv420p"] = "yuv420p"
    preset: Literal["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"] = "medium"
    crf: float = Field(default=20, ge=0, le=51)
    reframe: Reframe = Field(default_factory=Reframe)


class Audio(Model):
    normalize: bool = True
    target_lufs: float = Field(default=-16, ge=-70, le=-5)
    true_peak: float = Field(default=-1.5, ge=-9, le=0)
    source_audio: SourceAudio = Field(default_factory=SourceAudio)


class Captions(Model):
    style_preset: Literal["default", "premium"] = "default"
    highlight_keywords: bool = False
    highlight_color: str = Field(default="#FFD84D", pattern=r"^#[0-9a-fA-F]{6}$")
    keywords: list[str] = Field(default_factory=list, max_length=2)
    enabled: bool = True
    mode: Literal["narration", "source", "source_dialogue", "both"] = "narration"
    source_dialogue: bool = False
    whisper_model: str = "small"
    max_lines: int = Field(default=2, ge=1, le=2)
    max_chars_per_line: int = Field(default=34, ge=8, le=80)
    position: Literal["top", "center", "bottom"] = "bottom"
    margin_bottom: int = Field(default=230, ge=0, le=1500)
    style: Style = Field(default_factory=Style)


class Hook(Model):
    enabled: bool = True
    duration: float = Field(default=2.2, gt=0)
    position: Literal["top", "center", "bottom"] = "top"
    margin_top: int = Field(default=165, ge=0, le=1500)
    style: Style = Field(default_factory=Style)


class SourceLabel(Model):
    enabled: bool = True
    show_last_seconds: float = Field(default=2, gt=0)
    position: Literal["top", "center", "bottom"] = "bottom"
    margin_bottom: int = Field(default=90, ge=0, le=1500)


class Export(Model):
    container: Literal["mp4"] = "mp4"
    audio_codec: Literal["aac"] = "aac"
    audio_bitrate: str = Field(default="192k", pattern=r"^[1-9]\d{1,3}k$")
    faststart: bool = True
    filename_template: str = "{index:02d}-{slug}-{id}.mp4"
    write_metadata_sidecar: bool = True

    @field_validator("filename_template")
    @classmethod
    def template(cls, value):
        try:
            value.format(index=1, slug="short", id="id")
        except (ValueError, KeyError, IndexError, AttributeError) as exc:
            raise ValueError("use {index:02d}, {slug} e {id}") from exc
        if len(value) > 180:
            raise ValueError("template excede 180 caracteres")
        return value


class Transition(Model):
    type: Literal["cut", "fade", "crossfade"] = "cut"
    duration: float = Field(default=.15, gt=0, le=2)


class Gate(Model):
    enabled: bool = True
    warn_if_no_voiceover: bool = True
    warn_continuous_source_clip_over_seconds: float = Field(default=25, ge=0)
    warn_if_original_words_below: int = Field(default=20, ge=0)


class EndTag(Model):
    enabled: bool = False
    text: str = Field(default="Tô Assistindo Isso", min_length=1, max_length=32)
    secondary_text: str = Field(default="Curtiu? Tem mais.", max_length=40)
    icon: Literal["thumbs_up", "none"] = "thumbs_up"
    duration: float = Field(default=1, ge=.8, le=1.2)
    position: Literal["bottom_center"] = "bottom_center"


class Branding(Model):
    end_tag: EndTag = Field(default_factory=EndTag)


SETTINGS = {"video": Video, "audio": Audio, "captions": Captions, "hook": Hook,
            "source_label": SourceLabel, "export": Export, "transition": Transition,
            "transformative_gate": Gate, "voice": Voiceover, "branding": Branding, "editing": Editing}
