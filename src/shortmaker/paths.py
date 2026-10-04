from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]


def executable(name):
    found = shutil.which(name)
    if found:
        return found
    for folder in (Path.cwd() / "bin", ROOT / "bin"):
        candidate = folder / (name + ".exe")
        if candidate.is_file():
            return str(candidate.resolve())
    raise ValueError(f"{name} não encontrado. Instale FFmpeg no PATH ou coloque ffmpeg.exe e ffprobe.exe na pasta bin do projeto.")


def writable_output(folder):
    folder = Path(folder).resolve()
    try:
        folder.mkdir(parents=True, exist_ok=True)
        import tempfile
        with tempfile.TemporaryFile(dir=folder):
            pass
    except OSError as exc:
        raise ValueError(f"Pasta de saída sem permissão de escrita: {folder}") from exc
    return folder
