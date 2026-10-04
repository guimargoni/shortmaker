import re
import unicodedata
from pathlib import Path


def safe_name(value):
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value).strip(" .-")[:100] or "short"
    if value.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        value = "short-" + value
    return value


def output_path(folder, short, index):
    youtube = short.publishing.get("youtube", {}) or short.publishing.get("platforms", {}).get("youtube", {})
    slug = safe_name(youtube.get("title") or short.editorial.get("title") or short.id)
    try:
        name = short.export["filename_template"].format(index=index, slug=slug, id=safe_name(short.id))
    except (KeyError, ValueError, IndexError) as exc:
        raise ValueError("export.filename_template inválido; use {index:02d}, {slug} e {id}") from exc
    name = safe_name(Path(name).stem) + ".mp4"
    candidate = Path(folder) / name
    count = 2
    while candidate.exists() or candidate.with_suffix(".metadata.json").exists():
        candidate = Path(folder) / f"{Path(name).stem}-{count}.mp4"
        count += 1
    return candidate
