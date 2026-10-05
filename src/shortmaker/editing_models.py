from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Model(BaseModel):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)


class Effect(Model):
    type: Literal['punch_in', 'slow_zoom', 'freeze_frame', 'text_card', 'speed_change', 'fade', 'hard_cut_marker']
    at: float = Field(default=0, ge=0)
    duration: float | None = Field(default=None, gt=0, le=10)
    scale: float = Field(default=1.08, ge=1, le=1.25)
    start_at: float = Field(default=0, ge=0)
    end_at: float | None = Field(default=None, gt=0)
    from_scale: float = Field(default=1, ge=1, le=1.25)
    to_scale: float = Field(default=1.06, ge=1, le=1.25)
    speed: float = Field(default=1, ge=.75, le=1.35)
    audio_mode: Literal['continue', 'mute', 'duck'] = 'continue'
    text: str = Field(default='', max_length=120)
    style: Literal['editorial', 'impact', 'subtle'] = 'editorial'
    direction: Literal['in', 'out'] = 'in'
    background: bool = False

    @model_validator(mode='after')
    def intervals(self):
        if (self.type == 'speed_change' and self.end_at is None) or (self.type in {'slow_zoom', 'speed_change'} and self.end_at is not None and self.end_at <= self.start_at):
            raise ValueError('end_at deve exceder start_at')
        if self.type == 'text_card' and not self.text.strip():
            raise ValueError('text_card exige texto')
        if self.type == 'freeze_frame' and self.duration is not None and self.duration > 1.2:
            raise ValueError('freeze_frame máximo 1.2s')
        if self.type == 'fade' and self.duration is not None and self.duration > .4:
            raise ValueError('fade máximo 0.4s')
        return self


class TrimPolicy(Model):
    remove_dead_time: bool = False
    max_removal_ms: int = Field(default=650, ge=0, le=650)
    preserve_dialogue: bool = True
    preserve_reaction: bool = True


class Editing(Model):
    pace: Literal['dramatic', 'normal', 'fast'] = 'normal'
    editorial_quality_warnings: bool = False


