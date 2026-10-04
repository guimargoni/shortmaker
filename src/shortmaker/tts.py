"""Local Piper/SAPI workers; renderer still receives a WAV and its measured duration."""
import importlib.util
import json
import logging
import math
import os
from pathlib import Path
import re
import sys
import wave
from .ffmpeg_runner import Runner
from .paths import ROOT
from .pronunciation import apply_overrides

BENCHMARK = "Por mais de cem anos, eles acreditaram estar seguros. Até que isso apareceu."


def model_paths(voice_id):
    if not re.fullmatch(r"[a-z]{2}_[A-Z]{2}-[a-zA-Z0-9_]+-(?:low|medium|high|x_low)", voice_id):
        raise ValueError("voice_id inválido; use um identificador Piper, por exemplo pt_BR-faber-medium")
    folder = Path(os.environ.get("SHORTMAKER_PIPER_MODELS", str(ROOT / "models" / "piper")))
    model = folder / f"{voice_id}.onnx"
    return model, Path(str(model) + ".json")


def select_engine(voiceover):
    if voiceover.engine == "sapi":
        return "sapi", None
    if voiceover.engine != "piper":
        raise ValueError(f"Engine não suportada: {voiceover.engine}; use piper ou sapi")
    if importlib.util.find_spec("piper") is None:
        return "sapi", "Piper não instalado"
    model, config = model_paths(voiceover.voice_id)
    if not model.is_file() or not config.is_file():
        return "sapi", f"Modelo/configuração Piper indisponível: {voiceover.voice_id}"
    return "piper", None


def wav_duration(path):
    with wave.open(str(path), "rb") as audio:
        duration = audio.getnframes() / audio.getframerate()
    if duration <= 0:
        raise ValueError("TTS gerou áudio vazio; verifique o modelo/voz local")
    return duration


def synthesize(voiceover, output, runner, allow_fallback=True):
    runner.check()
    engine, reason = select_engine(voiceover)
    if reason and not allow_fallback:
        raise ValueError(reason + "; amostras Piper não usam fallback")
    request = Path(output).with_suffix(".tts.json")
    spoken_text, applied = apply_overrides(voiceover.text, voiceover.pronunciation_overrides)
    if applied:
        logging.info("Pronunciation overrides aplicados: %s", json.dumps(applied, ensure_ascii=False))
    def run_voice(selected):
        data = voiceover.model_dump()
        data["engine"] = selected
        data["text"] = spoken_text
        request.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        runner.run([sys.executable, "-m", "shortmaker.tts", "speak", request, output], timeout=120)
        return wav_duration(output)
    if reason:
        logging.warning("%s; fallback local SAPI", reason)
    try:
        duration = run_voice(engine)
    except (ValueError, OSError, EOFError, wave.Error) as exc:
        if engine != "piper" or not allow_fallback:
            raise ValueError(f"Falha na narração {engine}: {exc}. Verifique modelos Piper ou vozes SAPI instaladas.") from exc
        reason = f"Piper falhou ao gerar áudio: {exc}"
        logging.warning("%s; fallback local SAPI", reason)
        engine = "sapi"
        duration = run_voice(engine)
    logging.info("TTS solicitado=%s efetivo=%s voice_id=%s duração=%.3fs fallback=%s",
                 voiceover.engine, engine, voiceover.voice_id if engine == "piper" else None, duration, reason)
    Path(output).with_suffix(".tts.result.json").write_text(json.dumps({"requested_engine": voiceover.engine,
        "effective_engine": engine, "voice_id": voiceover.voice_id if engine == "piper" else None,
        "duration": duration, "fallback_reason": reason, "pronunciation_applied": applied}, ensure_ascii=False, indent=2), encoding="utf-8")
    return duration


def piper_worker(data, output):
    from piper import PiperVoice, SynthesisConfig
    model, config = model_paths(data["voice_id"])
    # load() with explicit local files; no download, server or CUDA initialization.
    voice = PiperVoice.load(model, config_path=config, use_cuda=False)
    settings = SynthesisConfig(length_scale=1 / data["rate"], volume=data["volume"])
    with wave.open(str(output), "wb") as wav:
        voice.synthesize_wav(data["text"], wav, syn_config=settings)
    wav_duration(output)


def samples():
    import argparse
    from .models import Voiceover
    parser = argparse.ArgumentParser(description="Compare duas vozes Piper com a mesma frase")
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "voice-samples")
    parser.add_argument("--rate", type=float, default=1)
    parser.add_argument("--volume", type=float, default=1)
    args = parser.parse_args(sys.argv[2:])
    args.output.mkdir(parents=True, exist_ok=True)
    for voice_id in ("pt_BR-faber-medium", "pt_BR-cadu-medium"):
        voiceover = Voiceover(enabled=True, engine="piper", voice_id=voice_id, text=BENCHMARK,
                              rate=args.rate, volume=args.volume)
        target = args.output / (voice_id + ".wav")
        if target.exists():
            raise ValueError(f"Amostra já existe: {target}; escolha outra pasta --output")
        duration = synthesize(voiceover, target, Runner(), allow_fallback=False)
        print(f"{voice_id}: {duration:.3f}s — {target.resolve()}", flush=True)


def worker():
    if sys.argv[1] == "samples":
        samples()
        return
    if sys.argv[1] == "speak":
        data = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        if data["engine"] == "piper":
            piper_worker(data, Path(sys.argv[3]).resolve())
            return
    import pyttsx3
    engine = pyttsx3.init("sapi5")
    voices = engine.getProperty("voices")
    if sys.argv[1] == "voices":
        print(json.dumps([{"id": v.id, "name": v.name, "languages": [str(x) for x in v.languages]} for v in voices], ensure_ascii=False))
        return
    data = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    selected = data.get("voice")
    if selected:
        matches = [v for v in voices if selected.lower() in (v.id + " " + v.name).lower()]
        if not matches:
            raise ValueError(f"Voz não instalada: {selected}")
        engine.setProperty("voice", matches[0].id)
    else:
        matches = [v for v in voices if "brazil" in v.name.lower() or "portugu" in v.name.lower() or "416" in str(v.languages)]
        if matches:
            engine.setProperty("voice", matches[0].id)
    engine.setProperty("rate", round(180 * data.get("rate", 1)))
    engine.setProperty("volume", data.get("volume", 1))
    output = str(Path(sys.argv[3]).resolve())
    try:
        engine.save_to_file(data["text"], output)
        engine.runAndWait()
        wav_duration(output)
    except (OSError, ValueError, EOFError):
        # Local fallback uses the same installed SAPI voices directly.
        import comtypes.client
        speaker = comtypes.client.CreateObject("SAPI.SpVoice")
        stream = comtypes.client.CreateObject("SAPI.SpFileStream")
        for token in speaker.GetVoices():
            if token.Id == engine.getProperty("voice"):
                speaker.Voice = token
        speaker.Rate = max(-10, min(10, round(10 * math.log2(data.get("rate", 1)))))
        speaker.Volume = round(100 * data.get("volume", 1))
        stream.Open(output, 3, False)
        try:
            speaker.AudioOutputStream = stream
            speaker.Speak(data["text"])
        finally:
            stream.Close()
        wav_duration(output)


if __name__ == "__main__":
    worker()
