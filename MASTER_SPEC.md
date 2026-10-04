# SHORTMAKER — MASTER SPEC v0.2

## 1. Non-negotiable product outcome

SHORTMAKER is a local-first Windows desktop application that turns **one source video + one JSON edit plan** into **finished vertical Shorts that do not require CapCut or manual editing before upload**.

The intended workflow is:

1. User selects a local video.
2. User pastes/loads a JSON generated externally (for example by ChatGPT).
3. User validates the plan.
4. User clicks **Generate Shorts**.
5. SHORTMAKER renders one or more final MP4s.
6. User only reviews: **Approve / Reject**.
7. Future versions may upload/schedule approved videos automatically.

The executor must not be an editorial AI. The JSON is the editorial source of truth.

## 2. What “finished” means

A PASS output must already contain, when configured by JSON:

- exact source excerpts;
- multi-segment montage;
- 9:16 framing at 1080x1920;
- original hook;
- original commentary/narration;
- generated voiceover;
- source-audio ducking under voiceover;
- captions for narration;
- optional captions/transcription of source dialogue;
- text overlays;
- source/work label;
- simple transitions where requested;
- audio normalization;
- H.264/AAC MP4 ready for upload.

The user must **not** need to reopen the result in CapCut.

## 3. Important monetization/copyright framing

The app cannot guarantee YouTube monetization or absence of copyright claims. Those decisions depend on rights holders and YouTube.

However, the app **must support a monetization-oriented transformative format**, meaning the JSON can create commentary, analysis, recommendation, curiosity/explainer, or narrative videos that use short source excerpts as supporting material rather than simple reposts.

The app should expose a `transformative_gate` warning system. It is only a heuristic and must never label a video as “guaranteed monetizable”.

## 4. MVP that must be completed first

### Required today / v0.2 MVP

- Windows desktop UI.
- Select source `.mp4`, `.mkv`, `.mov`, `.webm`.
- Paste/load JSON.
- Validate JSON with readable field paths.
- Generate multiple Shorts from one source.
- Timeline-based montage from multiple source excerpts.
- 1080x1920 export, no black bars in default crop mode.
- Hook overlay.
- Voiceover generation from JSON narration text.
- Offline TTS path required: Windows SAPI via `pyttsx3`.
- Optional higher-quality online-no-key engine may be added later, but must not be required.
- Voiceover mixed with source audio using ducking.
- Narration captions generated deterministically from narration text.
- Optional source-dialogue transcription via `faster-whisper` if enabled.
- Source label/end label.
- Audio loudness normalization.
- Sequential processing of all enabled Shorts.
- Progress, logs, cancellation.
- Open output folder.
- Tests for JSON, timecodes, inheritance, timeline validation, naming.

### Explicitly NOT required now

- YouTube OAuth/upload/scheduling.
- TikTok/Instagram upload.
- Analytics.
- Database.
- Server/cloud backend.
- Login/account system.
- Automatic scene discovery.
- Face tracking.
- Smart AI reframing.
- Complex transitions.
- Music catalog.
- Installer polish.

## 5. Mandatory stack

Use the smallest stack practical for same-day implementation:

- Python 3.11+
- Tkinter + ttk
- Pydantic v2
- FFmpeg / ffprobe via subprocess
- pyttsx3 for required local/offline narration
- faster-whisper only for optional source transcription
- ASS subtitle generation for captions/text overlays
- threading or ThreadPoolExecutor
- pathlib
- logging
- pytest

Do NOT introduce React, Electron, Tauri, FastAPI, Docker, Redis, DBs, web servers, or paid APIs.

## 6. Repository layout

```text
shortmaker/
├─ README.md
├─ MASTER_SPEC.md
├─ CODEX_PROMPT.md
├─ JSON_CONTRACT.md
├─ ACCEPTANCE_TESTS.md
├─ pyproject.toml
├─ requirements.txt
├─ .gitignore
├─ src/
│  └─ shortmaker/
│     ├─ __init__.py
│     ├─ app.py
│     ├─ constants.py
│     ├─ models.py
│     ├─ validation.py
│     ├─ timecodes.py
│     ├─ paths.py
│     ├─ logging_config.py
│     ├─ media_probe.py
│     ├─ ffmpeg_runner.py
│     ├─ tts.py
│     ├─ captions.py
│     ├─ ass_builder.py
│     ├─ audio.py
│     ├─ timeline.py
│     ├─ render_pipeline.py
│     ├─ output_naming.py
│     └─ gui/
│        ├─ __init__.py
│        └─ main_window.py
├─ tests/
│  ├─ test_models.py
│  ├─ test_timecodes.py
│  ├─ test_validation.py
│  ├─ test_inheritance.py
│  ├─ test_timeline.py
│  └─ test_output_naming.py
├─ examples/
│  ├─ minimal_transformative.example.json
│  └─ full_future.example.json
├─ schemas/
│  └─ shortmaker.schema.json
├─ output/
│  └─ .gitkeep
└─ logs/
   └─ .gitkeep
```

## 7. GUI

Keep it intentionally simple.

```text
SHORTMAKER
────────────────────────────────────────────

Vídeo fonte
[ C:\...\episodio.mkv                    ] [Selecionar]

Plano JSON
┌──────────────────────────────────────────┐
│                                          │
│ cole o JSON aqui                         │
│                                          │
└──────────────────────────────────────────┘
[Carregar JSON] [Validar]

Saída
[ C:\...\shortmaker\output               ] [Selecionar]

[ GERAR SHORTS ]   [ CANCELAR ]

Short 2/4 — renderizando
[███████████████---------] 64%

Status: gerando narração...

Log resumido
┌──────────────────────────────────────────┐
│ JSON válido                              │
│ Short 1 concluído                        │
└──────────────────────────────────────────┘

[Abrir pasta de saída]
```

Rules:
- Generate disabled until source exists + JSON valid.
- UI never blocks during render.
- readable errors, not raw stack traces.
- final files never overwritten silently.
- all current UI text may be Portuguese.

## 8. Timeline model

The key architectural change from v0.1 is that each Short is a **timeline**, not one continuous cut.

A Short contains ordered `segments`.

MVP segment type:

`source_clip`

Each source clip can contain:
- source start/end;
- optional speed;
- optional crop override;
- source audio mode;
- optional voiceover;
- optional overlay text;
- transition in/out.

Future segment types may include `image`, `text_card`, `generated_broll`, but they are not implemented now.

## 9. Voiceover behavior

Narration is fundamental, not decorative.

A `source_clip` segment may contain:

```json
"voiceover": {
  "enabled": true,
  "text": "Texto original...",
  "engine": "sapi",
  "voice": null,
  "rate": 1.0,
  "volume": 1.0,
  "duck_source_db": -16,
  "start_offset": 0.15
}
```

Implementation:
1. Generate narration WAV with pyttsx3.
2. Measure generated narration duration.
3. Mix narration over the source clip.
4. Reduce source audio under narration by configured amount.
5. If narration is longer than the selected visual segment by <= 1.5 s, hold final video frame for the small overflow.
6. If overflow > 1.5 s, fail that segment with a clear validation/render error so the editorial JSON can be corrected.

This prevents silent truncation of narration.

## 10. Narration captions

For narration, do NOT run Whisper unnecessarily.

Because the narration text is known, create caption chunks from the text itself.

Algorithm:
- split by punctuation;
- then wrap to max configured characters;
- distribute chunk timings proportionally by character count across actual synthesized voice duration;
- generate ASS events;
- max two lines by default.

This is deterministic, fast, and cheap.

If a segment has no voiceover and `captions.source_dialogue=true`, then use faster-whisper on that trimmed source segment.

## 11. Rendering strategy

Favor reliability over a giant single FFmpeg graph.

Per Short:

1. probe source;
2. create temp directory;
3. for each timeline segment:
   - validate source range;
   - synthesize voiceover if any;
   - produce ASS events;
   - render segment to a normalized intermediate MP4;
4. concat normalized segment MP4s;
5. apply short-level global overlays if any;
6. normalize final audio;
7. encode/move final MP4;
8. clean temp files;
9. report result.

All intermediate video files use the same dimensions/fps/pixel format/audio format to make concat reliable.

## 12. Vertical framing

Implement now:
- `center_crop`
- `manual`
- `fit_blur` only if trivial

Recognize but do not implement:
- `face_track`
- `smart_track`

If unimplemented mode is requested:
- log warning;
- fall back to `center_crop` unless `strict=true`.

Default 9:16 process:
- scale to cover 1080x1920;
- crop to 1080x1920;
- no black bars.

## 13. Hooks and text overlays

Use ASS, not many fragile drawtext calls.

Hook can be:
- visual text only;
- visual text + narration if JSON includes narration in first segment.

Default hook:
- first 1.8–2.8 sec;
- top safe area;
- large bold text;
- outline;
- no proprietary font dependency.

## 14. Source audio

Per segment:

`source_audio.mode`:
- `keep`
- `duck`
- `mute`

When voiceover exists, default is `duck`.

Default duck amount: around -16 dB relative reduction.

Final loudness target default: -16 LUFS, true peak about -1.5 dBTP.

## 15. Simple transitions

MVP supports:
- `cut`
- optional short `fade` if easy

Default is `cut`.

Do not spend time on fancy transitions.

## 16. JSON inheritance

Merge order:

1. application hard defaults;
2. top-level `defaults`;
3. short-level overrides;
4. segment-level overrides.

Deep-merge dictionaries.
Lists replace.
Unknown fields may be preserved/ignored when compatibility allows.

## 17. Transformative gate heuristic

This is a warning system only.

Possible warnings:
- no original voiceover/commentary anywhere;
- one continuous source clip > 25 sec with no commentary;
- total original narration words < configurable threshold;
- all segments preserve full source audio and add no analysis;

The UI should say:

`Aviso editorial: este plano parece ter pouca contribuição original. Isso não impede a renderização e não é uma avaliação oficial de monetização.`

Never say “monetization approved”.

## 18. Output metadata

JSON may contain future publishing metadata:
- title
- description
- tags
- platform metadata
- approval state
- schedule_at

v0.2 parses/preserves these but does not upload anything.

Optionally write a sibling metadata JSON beside each rendered MP4 so future YouTube integration can use it.

Example:

```text
01-aot-wall-fall.mp4
01-aot-wall-fall.metadata.json
```

## 19. Output naming

Default template:

`{index:02d}-{slug}-{id}.mp4`

Slug priority:
1. publishing.youtube.title
2. editorial.title
3. short.id

Sanitize Windows-illegal characters.
On collision append `-2`, `-3`, etc.

## 20. Dependency handling

FFmpeg:
- search PATH;
- search `./bin/ffmpeg.exe` and `./bin/ffprobe.exe`.

TTS:
- pyttsx3 must work with Windows SAPI without account/API key.
- expose available installed voices in logs/config if possible.
- do not block MVP on premium neural voices.

Whisper:
- only needed if source dialogue transcription is enabled.
- CPU must be supported.
- GPU optional.

## 21. Progress stages

- validating
- probing
- preparing_segment
- generating_voiceover
- generating_captions
- rendering_segment
- concatenating
- normalizing_audio
- finalizing
- completed
- failed
- cancelled

## 22. Error handling

Readable errors for:
- FFmpeg/ffprobe missing;
- invalid JSON;
- invalid source range;
- missing video stream;
- narration overflow > allowed amount;
- TTS failure;
- Whisper failure when requested;
- output folder unwritable;
- FFmpeg failure.

Detailed stack traces go to `logs/shortmaker.log`.

## 23. Same-day priorities

If time/credit becomes tight, the order is:

1. timeline + exact cuts;
2. 9:16 render;
3. local TTS;
4. ducking/mix;
5. narration captions;
6. hook overlay;
7. concat multiple segments;
8. multiple Shorts;
9. source label;
10. optional Whisper source dialogue.

Do not sacrifice the end-to-end transformative pipeline to implement optional polish.

## 24. Definition of Done

PASS only when all are true:

- Windows app launches.
- User selects a real video.
- User pastes a valid timeline JSON.
- App validates it.
- One Short with at least 3 source segments renders.
- At least 2 of those segments can contain original voiceover.
- Voiceover is audible and source audio ducks underneath.
- Narration captions appear.
- Hook appears.
- Output is 1080x1920 MP4.
- No black bars in default mode.
- Multiple Shorts in one JSON render sequentially.
- Output needs no mandatory CapCut/manual editing step.
- UI remains responsive.
- Errors are readable.
- Tests pass.
- README explains exact Windows setup/run.
- No server, DB, login, or paid API was introduced.

YouTube scheduling is explicitly a future milestone.
