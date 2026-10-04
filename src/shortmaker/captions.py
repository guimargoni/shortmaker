import re
import textwrap


def narration_events(text, duration, offset=0, width=34, max_lines=2):
    chunks = []
    for sentence in re.split(r"(?<=[.!?;:])\s+", text.strip()):
        lines = textwrap.wrap(sentence, width=width, break_long_words=True, break_on_hyphens=False)
        chunks.extend("\n".join(lines[i:i + max_lines]) for i in range(0, len(lines), max_lines))
    total = sum(len(c.replace("\n", "")) for c in chunks)
    events = []
    start = offset
    for chunk in chunks:
        end = start + duration * len(chunk.replace("\n", "")) / total
        events.append((start, end, chunk))
        start = end
    return events


def transcribe(audio_path, destination, settings, language, runner):
    import json
    from pathlib import Path
    import sys
    request = Path(destination).with_suffix(".request.json")
    request.write_text(json.dumps({"audio": str(audio_path), "settings": settings, "language": language}), encoding="utf-8")
    try:
        runner.run([sys.executable, "-m", "shortmaker.captions", request, destination], timeout=1800)
        return json.loads(Path(destination).read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ValueError(f"Falha na transcrição solicitada. Instale pip install 'shortmaker[transcription]' e disponibilize o modelo Whisper. {exc}") from exc


if __name__ == "__main__":
    import json
    from pathlib import Path
    import sys
    from faster_whisper import WhisperModel
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    model = WhisperModel(data["settings"].get("whisper_model", "small"), device="cpu", compute_type="int8")
    language = data.get("language")
    segments, _ = model.transcribe(data["audio"], language=language.split("-")[0] if language else None)
    events = []
    for segment in segments:
        events.extend(narration_events(segment.text, segment.end - segment.start, segment.start,
                                       data["settings"]["max_chars_per_line"], data["settings"]["max_lines"]))
    Path(sys.argv[2]).write_text(json.dumps(events, ensure_ascii=False), encoding="utf-8")
