"""Explicit one-time download of pinned, checksummed Piper models. No account needed."""
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / "docs/voices/manifest.json").read_text(encoding="utf-8"))
    target_dir = ROOT / "models/piper"
    target_dir.mkdir(parents=True, exist_ok=True)
    for item in manifest:
        for filename, info in item["files"].items():
            if filename == "MODEL_CARD":
                continue  # Original cards are versioned in docs/voices.
            target = target_dir / filename
            if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == info["sha256"]:
                print(f"Já verificado: {filename}")
                continue
            if target.exists():
                raise ValueError(f"Arquivo local diferente do manifesto: {target}; mova-o antes de reinstalar")
            temp = None
            try:
                with urllib.request.urlopen(info["url"], timeout=60) as response, tempfile.NamedTemporaryFile(dir=target_dir, delete=False) as output:
                    temp = Path(output.name)
                    digest = hashlib.sha256()
                    while chunk := response.read(1024 * 1024):
                        digest.update(chunk)
                        output.write(chunk)
                if digest.hexdigest() != info["sha256"]:
                    raise ValueError(f"SHA256 divergente: {filename}")
                temp.rename(target)
                print(f"Instalado e verificado: {filename}")
            finally:
                if temp:
                    temp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
