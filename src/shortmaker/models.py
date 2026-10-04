from typing import Annotated, Any, Literal
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator, model_validator
from .timecodes import seconds

Time = Annotated[float, BeforeValidator(seconds)]


class Model(BaseModel):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)


class Voiceover(Model):
    enabled: bool = False
    text: str = ""
    engine: str = "sapi"
    voice: str | None = None
    voice_id: str = Field(default="pt_BR-faber-medium", pattern=r"^[a-z]{2}_[A-Z]{2}-[a-zA-Z0-9_]+-(?:low|medium|high|x_low)$")
    rate: float = Field(default=1, gt=0, le=4)
    volume: float = Field(default=1, ge=0, le=1)
    start_offset: float = Field(default=0, ge=0)
    duck_source_db: float | None = Field(default=None, le=0)
    pronunciation_overrides: dict[str, str] = Field(default_factory=dict)

    @field_validator("pronunciation_overrides")
    @classmethod
    def check_overrides(cls, value):
        if any(not key.strip() or not replacement.strip() for key, replacement in value.items()):
            raise ValueError("pronunciation_overrides exige nomes e pronúncias não vazios")
        return value

    @model_validator(mode="after")
    def check_text(self):
        if self.enabled and not self.text.strip():
            raise ValueError("narração habilitada exige text não vazio")
        return self


class SourceAudio(Model):
    mode: Literal["keep", "duck", "mute"] = "duck"
    duck_db: float = Field(default=-16, le=0)


class CropKeyframe(Model):
    at: float = Field(ge=0)
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class Reframe(Model):
    mode: Literal["center_crop", "manual", "face_track", "smart_track", "fit_blur", "anime_face_track", "manual_keyframes"] = "center_crop"
    strict: bool = False
    zoom: float = Field(default=1, ge=1, le=10)
    manual_x: float | None = Field(default=None, ge=0, le=1)
    manual_y: float | None = Field(default=None, ge=0, le=1)
    keyframes: list[CropKeyframe] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_keyframes(self):
        if self.mode == "manual_keyframes" and not self.keyframes:
            raise ValueError("manual_keyframes exige ao menos um keyframe")
        if any(b.at <= a.at for a, b in zip(self.keyframes, self.keyframes[1:])):
            raise ValueError("keyframes.at devem estar em ordem estritamente crescente")
        return self


class Segment(Model):
    id: str = ""
    type: Literal["source_clip"]
    start: Time
    end: Time
    speed: float = Field(default=1, gt=0, le=16)
    voiceover: Voiceover = Field(default_factory=Voiceover)
    source_audio: SourceAudio = Field(default_factory=SourceAudio)
    reframe: Reframe = Field(default_factory=Reframe)
    overlay_text: str | dict | None = None
    transition_in: dict = Field(default_factory=dict)
    transition_out: dict = Field(default_factory=dict)
    captions: dict = Field(default_factory=dict)

    @field_validator("end")
    @classmethod
    def check_range(cls, value, info):
        if "start" in info.data and value <= info.data["start"]:
            raise ValueError("end deve ser maior que start")
        return value


class Short(Model):
    id: str = Field(min_length=1)
    enabled: bool = True
    editorial: dict = Field(default_factory=dict)
    timeline: list[Segment] = Field(min_length=1)
    video: dict = Field(default_factory=dict)
    audio: dict = Field(default_factory=dict)
    voice: dict = Field(default_factory=dict)
    captions: dict = Field(default_factory=dict)
    branding: dict = Field(default_factory=dict)
    hook: dict = Field(default_factory=dict)
    source_label: dict = Field(default_factory=dict)
    export: dict = Field(default_factory=dict)
    transformative_gate: dict = Field(default_factory=dict)
    publishing: dict = Field(default_factory=dict)


class Plan(Model):
    schema_version: str = Field(pattern=r"^1\.\d+$")
    project: dict = Field(default_factory=dict)
    defaults: dict = Field(default_factory=dict)
    shorts: list[Short] = Field(min_length=1)
    publishing: dict = Field(default_factory=dict)
    compatibility: dict = Field(default_factory=dict)
