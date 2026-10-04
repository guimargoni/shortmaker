"""Windows acceptance evidence. Requires real FFmpeg, Tk and installed SAPI.

Run these outside a sandbox that denies Windows COM/Tcl access.
"""
import array
import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from threading import Event, Thread
import time
import tkinter as tk
import wave
import pytest
from shortmaker.ffmpeg_runner import Runner, Cancelled
from shortmaker.paths import executable
from shortmaker.render_pipeline import Pipeline
from shortmaker.validation import parse_plan
from shortmaker.models import Voiceover
from shortmaker.tts import synthesize


def test_missing_ffmpeg_is_readable(monkeypatch, tmp_path):
    import shortmaker.paths as paths
    monkeypatch.setattr(paths.shutil, "which", lambda _: None)
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="ffmpeg não encontrado.*pasta bin"):
        executable("ffmpeg")


def test_cancel_active_process_and_future_work():
    cancel = Event()
    runner = Runner(cancel)
    thread = Thread(target=lambda: (time.sleep(.4), cancel.set()))
    thread.start()
    started = time.monotonic()
    with pytest.raises(Cancelled):
        runner.run([sys.executable, "-c", "import time;time.sleep(30)"])
    thread.join()
    assert time.monotonic() - started < 5
    with pytest.raises(Cancelled):
        runner.run([sys.executable, "-c", "raise Exception('must not run')"])


@pytest.mark.skipif(os.name != "nt", reason="Windows runtime")
def test_gui_boot_validation_responsive_cancel_and_open(tmp_path, monkeypatch):
    from shortmaker.gui.main_window import MainWindow
    root = tk.Tk()
    root.withdraw()
    window = MainWindow(root)
    try:
        assert str(window.generate["state"]) == "disabled"
        source = tmp_path / "video.mp4"
        source.touch()
        window.source.set(str(source))
        window.text.insert("1.0", json.dumps({"schema_version": "1.1", "shorts": [{"id": "test", "timeline": [{"type": "source_clip", "start": 0, "end": 1}]}]}))
        root.update()
        window.validate()
        root.update()
        assert str(window.generate["state"]) == "normal"
        window.text.insert("end", " ")
        root.update()
        assert str(window.generate["state"]) == "disabled"
        window.validate()
        fired = []
        root.after(50, lambda: fired.append(True))
        def simulated_work(*_):
            window.queue.put(("progress", ("rendering_segment", 40, "Short 1/2")))
            while not window.cancel.wait(.01):
                pass
            window.queue.put(("done", "Cancelado"))
        monkeypatch.setattr(window, "work", simulated_work)
        window.start()
        until = time.monotonic() + .5
        while time.monotonic() < until:
            root.update()
            time.sleep(.01)
        assert fired and window.busy
        assert window.bar["value"] == 40
        window.cancel_button.invoke()
        window.worker.join(timeout=2)
        until = time.monotonic() + .3
        while time.monotonic() < until:
            root.update()
            time.sleep(.01)
        assert not window.busy
        opened = []
        monkeypatch.setattr(os, "startfile", lambda path: opened.append(path))
        window.output.set(str(tmp_path))
        window.open_output()
        assert opened == [str(tmp_path)]
    finally:
        window.close()


def read_audio(path):
    with wave.open(str(path), "rb") as wav:
        values = array.array("h", wav.readframes(wav.getnframes()))
        return values, wav.getframerate()


def tone_strength(samples, rate, start, end, hz=997):
    samples = samples[round(start * rate):round(end * rate)]
    a = sum(v * math.cos(2 * math.pi * hz * i / rate) for i, v in enumerate(samples))
    b = sum(v * math.sin(2 * math.pi * hz * i / rate) for i, v in enumerate(samples))
    return 2 * math.hypot(a, b) / len(samples)


@pytest.mark.skipif(os.name != "nt", reason="Windows SAPI")
def test_real_sapi_montage_ducking_frames_and_failure(tmp_path):
    runner = Runner()
    ffmpeg = executable("ffmpeg")
    source = tmp_path / "source.mp4"
    runner.run([ffmpeg, "-v", "error", "-y", "-f", "lavfi", "-i", "color=red:s=640x360:r=15:d=4",
                "-f", "lavfi", "-i", "color=green:s=640x360:r=15:d=4", "-f", "lavfi", "-i", "color=blue:s=640x360:r=15:d=4",
                "-f", "lavfi", "-i", "sine=frequency=997:sample_rate=48000:duration=12",
                "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]", "-map", "[v]", "-map", "3:a", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", source])
    voiced = Voiceover(enabled=True, text="Ação e segurança.")
    voice_path = tmp_path / "voice.wav"
    voice_length = synthesize(voiced, voice_path, runner)
    values, _ = read_audio(voice_path)
    assert voice_length > .3 and max(abs(v) for v in values) > 100
    first = {"id": "montage", "editorial": {"hook_text": "Ação: você percebeu?", "source_label_text": "Fonte — teste"}, "timeline": [
        {"type": "source_clip", "start": 8.25, "end": 11.25, "voiceover": voiced.model_dump()},
        {"type": "source_clip", "start": .25, "end": 3.25, "source_audio": {"mode": "keep"}},
        {"type": "source_clip", "start": 4.25, "end": 7.25, "voiceover": voiced.model_dump()}]}
    broken = copy.deepcopy(first)
    broken["id"] = "broken"
    broken["timeline"][0]["end"] = 50
    second = {"id": "second", "timeline": [{"type": "source_clip", "start": .5, "end": 1.5}]}
    data = {"schema_version": "1.1", "defaults": {"video": {"preset": "ultrafast", "crf": 25}, "audio": {"normalize": False}}, "shorts": [first, broken, second]}
    stages = []
    outputs, failures = Pipeline(progress=lambda stage, pct, msg: stages.append((stage, msg))).render(source, parse_plan(data), tmp_path / "out")
    assert len(outputs) == 2 and len(failures) == 1
    assert "timeline[0].end" in failures[0]
    assert outputs[0].exists() and outputs[1].exists()
    assert any(stage == "failed" for stage, _ in stages)
    completed = [msg for stage, msg in stages if stage == "completed"]
    assert "montage" in completed[0] and "second" in completed[1]
    info = json.loads(runner.run([executable("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", outputs[0]]))
    video, audio = info["streams"][:2]
    assert (video["width"], video["height"], video["codec_name"], audio["codec_name"]) == (1080, 1920, "h264", "aac")
    assert abs(float(info["format"]["duration"]) - 9) < .25
    # Sample center and corners at known offsets: blue, red, green; no added black bars.
    for t, channel in ((.7, 2), (3.7, 0), (6.7, 1)):
        image = tmp_path / f"frame-{t}.rgb"
        runner.run([ffmpeg, "-v", "error", "-y", "-ss", t, "-i", outputs[0], "-vf", "scale=3:3", "-frames:v", 1, "-pix_fmt", "rgb24", "-f", "rawvideo", image])
        rgb = image.read_bytes()
        for offset in (0, 12, 24):
            pixel = rgb[offset:offset + 3]
            assert pixel[channel] > 70 and pixel[channel] > max(pixel[(channel + 1) % 3], pixel[(channel + 2) % 3]) * 1.5
    wav = tmp_path / "mix.wav"
    runner.run([ffmpeg, "-v", "error", "-y", "-i", outputs[0], "-vn", "-ac", 1, "-ar", 48000, "-c:a", "pcm_s16le", wav])
    mixed, rate = read_audio(wav)
    duck = tone_strength(mixed, rate, .2, min(voice_length - .1, 1))
    keep = tone_strength(mixed, rate, 3.2, 4)
    attenuation = 20 * math.log10(duck / keep)
    assert -20 < attenuation < -12, attenuation
    restored = tone_strength(mixed, rate, 2.5, 2.9)
    assert abs(20 * math.log10(restored / keep)) < 2
    assert outputs[0].with_suffix(".metadata.json").is_file()
    # Full decoder pass confirms playable MP4 without corrupt packets.
    runner.run([ffmpeg, "-v", "error", "-i", outputs[0], "-f", "null", "-"])


@pytest.mark.parametrize("changes,path", [({"video": {"reframe": None}}, "defaults.video.reframe"),
    ({"captions": {"max_lines": 0}}, "defaults.captions.max_lines"),
    ({"audio": {"target_lufs": "bad"}}, "defaults.audio.target_lufs"),
    ({"export": {"filename_template": "{unknown}"}}, "defaults.export.filename_template")])
def test_bad_settings_paths(changes, path):
    data = {"schema_version": "1.1", "defaults": changes, "shorts": [{"id": "test", "timeline": [{"type": "source_clip", "start": 0, "end": 1}]}]}
    with pytest.raises(ValueError) as error:
        parse_plan(data)
    assert path in str(error.value)
