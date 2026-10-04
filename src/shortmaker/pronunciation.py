import re


def apply_overrides(text, overrides):
    """Single-pass whole-word substitution; exact case wins before insensitive lookup."""
    if not overrides:
        return text, []
    pattern = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(key) for key in sorted(overrides, key=len, reverse=True)) + r")(?!\w)", re.IGNORECASE)
    applied = []
    def replace(match):
        original = match.group()
        key = original if original in overrides else next(key for key in overrides if re.fullmatch(re.escape(key), original, re.IGNORECASE))
        replacement = overrides[key]
        applied.append({"matched": original, "key": key, "replacement": replacement})
        return replacement
    return pattern.sub(replace, text), applied
