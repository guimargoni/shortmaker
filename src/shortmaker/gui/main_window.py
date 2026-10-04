import json
import logging
import os
from pathlib import Path
from queue import Queue, Empty
from threading import Event, Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ..ffmpeg_runner import Cancelled, Runner
from ..paths import ROOT, executable
from ..render_pipeline import Pipeline
from ..review import mark_review
from ..tts import select_engine
from ..validation import parse_plan, editorial_warnings


class MainWindow(ttk.Frame):
    def __init__(self, root):
        super().__init__(root, padding=16)
        self.root = root
        self.pack(fill="both", expand=True)
        root.title("SHORTMAKER 0.2")
        root.geometry("900x780")
        root.minsize(700, 650)
        self.source = tk.StringVar()
        self.output = tk.StringVar(value=str(ROOT / "output"))
        self.status = tk.StringVar(value="Selecione um vídeo e valide o JSON")
        self.plan = None
        self.busy = False
        self.cancel = Event()
        self.queue = Queue()
        self.review_files = []
        self.review_selection = tk.StringVar()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(11, weight=1)
        ttk.Label(self, text="SHORTMAKER", font=("Segoe UI", 20, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Vídeo fonte").grid(row=1, column=0, sticky="w", pady=(12, 3))
        source_row = ttk.Frame(self)
        source_row.grid(row=2, column=0, sticky="ew")
        source_row.columnconfigure(0, weight=1)
        self.source_entry = ttk.Entry(source_row, textvariable=self.source)
        self.source_entry.grid(row=0, column=0, sticky="ew")
        self.source_button = ttk.Button(source_row, text="Selecionar", command=self.select_source)
        self.source_button.grid(row=0, column=1, padx=(8, 0))
        text_box = ttk.LabelFrame(self, text="Plano JSON")
        text_box.grid(row=3, column=0, sticky="nsew", pady=12)
        self.text = tk.Text(text_box, height=13, wrap="word", undo=True)
        scroll = ttk.Scrollbar(text_box, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.text.pack(fill="both", expand=True)
        controls = ttk.Frame(self)
        controls.grid(row=4, column=0, sticky="w")
        self.load_button = ttk.Button(controls, text="Carregar JSON", command=self.load_json)
        self.load_button.pack(side="left")
        self.validate_button = ttk.Button(controls, text="Validar", command=self.validate)
        self.validate_button.pack(side="left", padx=8)
        ttk.Label(self, text="Saída").grid(row=5, column=0, sticky="w", pady=(10, 3))
        output_row = ttk.Frame(self)
        output_row.grid(row=6, column=0, sticky="ew")
        output_row.columnconfigure(0, weight=1)
        self.output_entry = ttk.Entry(output_row, textvariable=self.output)
        self.output_entry.grid(row=0, column=0, sticky="ew")
        self.output_button = ttk.Button(output_row, text="Selecionar", command=self.select_output)
        self.output_button.grid(row=0, column=1, padx=(8, 0))
        actions = ttk.Frame(self)
        actions.grid(row=7, column=0, sticky="w", pady=12)
        self.generate = ttk.Button(actions, text="GERAR SHORTS", command=self.start, state="disabled")
        self.generate.pack(side="left")
        self.cancel_button = ttk.Button(actions, text="CANCELAR", command=self.cancel.set, state="disabled")
        self.cancel_button.pack(side="left", padx=8)
        self.bar = ttk.Progressbar(self, maximum=100)
        self.bar.grid(row=8, column=0, sticky="ew")
        ttk.Label(self, textvariable=self.status, wraplength=820).grid(row=9, column=0, sticky="w", pady=8)
        ttk.Label(self, text="Log resumido").grid(row=10, column=0, sticky="w")
        self.log = tk.Text(self, height=7, state="disabled", wrap="word")
        self.log.grid(row=11, column=0, sticky="nsew")
        ttk.Button(self, text="Abrir pasta de saída", command=self.open_output).grid(row=12, column=0, sticky="w", pady=(12, 0))
        review_row = ttk.LabelFrame(self, text="Revisão local")
        review_row.grid(row=13, column=0, sticky="ew", pady=(10, 0))
        review_row.columnconfigure(0, weight=1)
        self.review_box = ttk.Combobox(review_row, textvariable=self.review_selection, state="readonly")
        self.review_box.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        for column, (label, action) in enumerate((("Reproduzir", self.play), ("Aprovar", lambda: self.review(True)), ("Rejeitar", lambda: self.review(False))), 1):
            ttk.Button(review_row, text=label, command=action).grid(row=0, column=column, padx=4)
        self.text.bind("<<Modified>>", self.changed)
        self.source.trace_add("write", lambda *_: self.update_generate())
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.poll_id = root.after(100, self.poll)

    def append(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def changed(self, _=None):
        if self.text.edit_modified():
            self.plan = None
            self.update_generate()
            self.text.edit_modified(False)

    def update_generate(self):
        ready = not self.busy and self.plan is not None and Path(self.source.get()).is_file() and any(s.enabled for s in self.plan.shorts)
        self.generate.configure(state="normal" if ready else "disabled")

    def select_source(self):
        path = filedialog.askopenfilename(filetypes=[("Vídeos", "*.mp4 *.mkv *.mov *.webm"), ("Todos", "*.*")])
        if path:
            self.source.set(path)

    def select_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output.set(path)

    def load_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8-sig")
            self.text.delete("1.0", "end")
            self.text.insert("1.0", content)
            self.text.edit_modified(False)
            self.plan = None
            self.validate()
        except (OSError, UnicodeError) as exc:
            messagebox.showerror("Erro", f"Não foi possível carregar JSON: {exc}")

    def validate(self):
        try:
            self.text.edit_modified(False)
            self.plan = parse_plan(self.text.get("1.0", "end"))
            self.status.set("JSON válido")
            self.append("JSON válido")
            for warning in editorial_warnings(self.plan):
                self.append(warning)
        except (ValueError, TypeError) as exc:
            self.plan = None
            self.status.set("JSON inválido")
            self.append(str(exc))
            messagebox.showerror("Validação", str(exc))
        self.update_generate()

    def set_busy(self, value):
        self.busy = value
        for widget in (self.load_button, self.validate_button, self.source_entry, self.source_button, self.output_entry, self.output_button):
            widget.configure(state="disabled" if value else "normal")
        self.text.configure(state="disabled" if value else "normal")
        self.cancel_button.configure(state="normal" if value else "disabled")
        self.update_generate()

    def start(self):
        if self.busy or self.plan is None:
            return
        self.cancel.clear()
        self.bar["value"] = 0
        self.set_busy(True)
        source, plan, output = self.source.get(), self.plan, self.output.get()
        self.worker = Thread(target=self.work, args=(source, plan, output), daemon=True)
        self.worker.start()

    def work(self, source, plan, output):
        try:
            executable("ffmpeg")
            executable("ffprobe")
            narrations = [seg.voiceover for short in plan.shorts if short.enabled for seg in short.timeline if seg.voiceover.enabled]
            for narration in narrations:
                engine, reason = select_engine(narration)
                self.queue.put(("log", f"Voz: {engine} / {narration.voice_id if engine == 'piper' else 'SAPI'}" + (f" — {reason}; fallback SAPI" if reason else "")))
            if any(select_engine(narration)[0] == "sapi" for narration in narrations):
                voices = Runner(self.cancel).run([__import__("sys").executable, "-m", "shortmaker.tts", "voices"], timeout=30)
                self.queue.put(("log", "Vozes SAPI instaladas: " + voices.strip()))
            outputs, failures = Pipeline(self.cancel, lambda *event: self.queue.put(("progress", event))).render(source, plan, output)
            self.queue.put(("outputs", outputs))
            self.queue.put(("done", f"Concluído: {len(outputs)} Short(s), {len(failures)} falha(s)"))
        except Cancelled:
            self.queue.put(("done", "Cancelado; saídas concluídas foram preservadas"))
        except Exception as exc:
            logging.exception("Falha na execução")
            self.queue.put(("done", str(exc)))

    def poll(self):
        try:
            while True:
                kind, data = self.queue.get_nowait()
                if kind == "progress":
                    stage, pct, message = data
                    self.bar["value"] = pct
                    self.status.set(f"{stage}: {message}")
                    self.append(message)
                elif kind == "log":
                    self.append(data)
                elif kind == "outputs":
                    self.review_files.extend(data)
                    self.review_box["values"] = [p.name for p in self.review_files]
                    if data:
                        self.review_box.current(len(self.review_files) - len(data))
                else:
                    self.status.set(data)
                    self.append(data)
                    self.set_busy(False)
        except Empty:
            pass
        self.poll_id = self.root.after(100, self.poll)

    def open_output(self):
        try:
            folder = Path(self.output.get()).resolve()
            folder.mkdir(parents=True, exist_ok=True)
            os.startfile(str(folder))
        except OSError as exc:
            messagebox.showerror("Erro", f"Não foi possível abrir pasta: {exc}")

    def selected_video(self):
        index = self.review_box.current()
        return self.review_files[index] if index >= 0 else None

    def play(self):
        video = self.selected_video()
        if video:
            try:
                os.startfile(str(video))
            except OSError as exc:
                messagebox.showerror("Erro", f"Não foi possível reproduzir vídeo: {exc}")

    def review(self, approved):
        video = self.selected_video()
        if video:
            try:
                mark_review(video, approved)
                self.append(f"{video.name}: {'aprovado' if approved else 'rejeitado'} localmente")
            except (OSError, ValueError) as exc:
                messagebox.showerror("Erro", f"Não foi possível salvar revisão: {exc}")

    def close(self):
        self.cancel.set()
        if self.busy and hasattr(self, "worker") and self.worker.is_alive():
            self.status.set("Cancelando antes de fechar...")
            self.root.after(100, self.close)
            return
        self.root.after_cancel(self.poll_id)
        self.root.destroy()
