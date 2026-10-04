import math
import re


def seconds(value):
    if isinstance(value, bool):
        raise ValueError("timecode deve ser número ou HH:MM:SS.mmm")
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str) and re.fullmatch(r"(?:\d{2}:)?[0-5]?\d:[0-5]\d(?:\.\d{1,3})?", value):
        result = 0.0
        for part in value.split(":"):
            result = result * 60 + float(part)
    else:
        raise ValueError("timecode inválido; use segundos ou HH:MM:SS.mmm")
    if not math.isfinite(result) or result < 0:
        raise ValueError("timecode deve ser finito e não negativo")
    return result
