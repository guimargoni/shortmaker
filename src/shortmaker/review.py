import json
from pathlib import Path
import tempfile


def mark_review(video, approved):
    video = Path(video)
    sidecar = video.with_suffix(".metadata.json")
    data = json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else {"short": {"publishing": {}}}
    publishing = data.setdefault("short", {}).setdefault("publishing", {})
    publishing["approved"] = approved
    publishing["approval_state"] = "approved" if approved else "rejected"
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", dir=sidecar.parent, delete=False) as file:
        temp = Path(file.name)
        json.dump(data, file, ensure_ascii=False, indent=2)
    try:
        temp.replace(sidecar)
    finally:
        temp.unlink(missing_ok=True)
    return sidecar
