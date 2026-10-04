import argparse
import json
from pathlib import Path
from threading import Event
import tkinter as tk
from .ffmpeg_runner import Cancelled
from .logging_config import configure
from .render_pipeline import Pipeline
from .validation import parse_plan


def main():
    parser = argparse.ArgumentParser(description="SHORTMAKER — vídeo + JSON → Shorts locais")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()
    configure()
    if args.source or args.plan:
        if not args.source or not args.plan:
            parser.error("--source e --plan são necessários juntos")
        try:
            plan = parse_plan(args.plan.read_text(encoding="utf-8-sig"))
            outputs, failures = Pipeline(progress=lambda stage, pct, msg: print(f"{pct:.0f}% {stage}: {msg}", flush=True)).render(args.source, plan, args.output)
            print(json.dumps({"outputs": [str(x) for x in outputs], "failures": failures}, ensure_ascii=False))
            return 1 if failures else 0
        except (ValueError, OSError, Cancelled) as exc:
            print(f"Erro: {exc}")
            return 1
    from .gui.main_window import MainWindow
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
