r"""Manual/reproducible real-episode GUI smoke test (not collected by pytest).

Usage: python tests/smoke_real_gui.py "C:\videos\episode.mkv"
"""
import json
from pathlib import Path
import sys
import time
import tkinter as tk
from shortmaker.gui.main_window import MainWindow
from shortmaker.logging_config import configure


configure()
root = tk.Tk()
root.withdraw()
window = MainWindow(root)
window.source.set(sys.argv[1])
window.output.set(str(Path("output/m3-gui").resolve()))
window.text.insert("1.0", Path("examples/m3_real_source.json").read_text(encoding="utf-8"))
root.update()
window.validate()
assert str(window.generate["state"]) == "normal"
heartbeat = []


def tick():
    heartbeat.append(time.monotonic())
    root.after(100, tick)


tick()
window.start()
until = time.monotonic() + 300
while window.busy and time.monotonic() < until:
    root.update()
    time.sleep(.01)
assert not window.busy, "render timed out"
assert len(window.review_files) == 2, window.log.get("1.0", "end")
assert len(heartbeat) > 10
assert max(b - a for a, b in zip(heartbeat, heartbeat[1:])) < 1
window.review(True)
sidecar = window.review_files[0].with_suffix(".metadata.json")
assert json.loads(sidecar.read_text(encoding="utf-8"))["short"]["publishing"]["approved"]
window.review(False)
print(json.dumps({"status": window.status.get(), "outputs": [str(p) for p in window.review_files],
                  "gui_heartbeats": len(heartbeat), "max_heartbeat_gap": max(b - a for a, b in zip(heartbeat, heartbeat[1:]))}, ensure_ascii=False))
window.close()
