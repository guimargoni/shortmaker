from dataclasses import dataclass
from fractions import Fraction
import json
import math
from .paths import executable
from .ffmpeg_runner import Runner


@dataclass
class Media:
    duration: float
    fps: float
    audio: bool
    width: int
    height: int


def probe(path, runner=None):
    data = json.loads((runner or Runner()).run([executable("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", path]))
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        raise ValueError("Vídeo fonte não contém uma faixa de vídeo")
    try:
        fps = float(Fraction(video.get("avg_frame_rate", "30/1")))
    except (ValueError, ZeroDivisionError):
        fps = 30
    duration = float(data["format"].get("duration", video.get("duration", 0)))
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Não foi possível determinar duração do vídeo")
    return Media(duration, fps if 0 < fps <= 120 else 30,
                 any(s["codec_type"] == "audio" for s in data["streams"]), video["width"], video["height"])
