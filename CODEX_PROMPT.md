# CODEX TASK — IMPLEMENT SHORTMAKER v0.2 END-TO-END TODAY

Repository: `guimargoni/shortmaker`

Read these files completely before coding:

1. `MASTER_SPEC.md`
2. `JSON_CONTRACT.md`
3. `ACCEPTANCE_TESTS.md`
4. `schemas/shortmaker.schema.json`
5. `examples/minimal_transformative.example.json`
6. `examples/full_future.example.json`

## Mission

Implement the smallest complete local Windows application that turns:

`source video + JSON timeline -> finished transformative vertical Shorts`

The user must not need CapCut after rendering.

## Do not redesign

Product and architecture decisions are already made.
Do not explore alternative frameworks.
Do not add infrastructure.
Do not broaden scope.
Do not build YouTube integration yet.

## Mandatory stack

- Python 3.11+
- Tkinter/ttk
- Pydantic v2
- FFmpeg/ffprobe subprocess
- pyttsx3 / Windows SAPI for required local voiceover
- ASS for narration captions and text overlays
- faster-whisper only when source-dialogue transcription is explicitly enabled
- pytest

No React/Electron/Tauri/FastAPI/DB/Docker/Redis/cloud backend/paid API.

## Implementation priority

### P0 — end-to-end path first

Before polishing architecture, make one real Short work with:

1. select source;
2. parse JSON;
3. render 3 source segments;
4. 1080x1920 center crop;
5. generate SAPI voiceover on at least 2 segments;
6. duck source audio under voiceover;
7. generate narration captions from known text;
8. add hook;
9. concatenate segments;
10. produce final MP4.

This is the critical product proof.

### P1 — multiple Shorts + validation

- robust models
- defaults inheritance
- multiple Shorts sequentially
- field-path errors
- output naming
- progress/logging/cancel

### P2 — optional source transcription

Only after P0/P1 pass:
- faster-whisper source dialogue captions when requested.

Do not let Whisper delay the core transformative renderer.

## Credit-saving rules

- No framework comparison.
- No large speculative refactors.
- No premature plugin architecture.
- No future publishing implementation.
- No fancy editor/timeline UI.
- No face tracking.
- No complex animation system.
- Prefer simple temp segment renders + concat over one giant FFmpeg graph.
- Run targeted tests while developing; full suite at gates.

## Technical implementation guidance

Use a deterministic intermediate-segment pipeline:

1. ffprobe source once;
2. for each source_clip segment:
   - trim source range;
   - generate voiceover WAV if enabled;
   - measure narration duration;
   - build ASS caption events from narration text;
   - center-crop/scale to 1080x1920;
   - mix audio, ducking source under narration;
   - render normalized segment MP4;
3. concat normalized segments;
4. apply short-level source label/global overlay if needed;
5. final loudness normalization and MP4 output.

Narration overflow:
- <= 1.5 sec: freeze last frame for overflow;
- > 1.5 sec: fail with clear actionable error.

Captions from narration:
- no Whisper;
- split punctuation/wrap;
- distribute by character proportion across actual TTS duration.

## Milestones

### M0 — skeleton and contract
PASS when:
- package boots;
- GUI selects video/JSON/output;
- models + inheritance + validation work;
- tests for JSON/timecodes/naming pass.

### M1 — core montage
PASS when:
- 3 source segments render to one vertical MP4;
- exact ordering and center crop work;
- no black bars.

### M2 — transformative layer
PASS when:
- SAPI voiceover works;
- source audio ducks;
- narration captions render;
- hook renders;
- multiple Shorts render sequentially.

### M3 — product gate
PASS when every acceptance test marked required in `ACCEPTANCE_TESTS.md` passes, README is complete, and a user can render without CapCut.

## Stop conditions

STOP only if:
- repo/environment is unwritable;
- FFmpeg requirement cannot work on target Windows environment;
- Windows SAPI cannot generate audio in the environment and there is no reasonable local fallback;
- the spec contains a blocking contradiction.

Do not stop for:
- missing GPU;
- optional Whisper feature;
- visual polish;
- unimplemented future schema fields;
- advanced transitions.

## Final response format

Return only a concise implementation report containing:

- milestone status: M0/M1/M2/M3 PASS or BLOCKED;
- files changed;
- test commands and results;
- manual smoke-test steps;
- known limitations;
- exact next user action.

Do not start YouTube scheduling.
