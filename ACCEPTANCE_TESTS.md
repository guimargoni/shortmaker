# SHORTMAKER v0.2 — Acceptance Tests

## Gate A — boot and dependencies

- [x] App starts on Windows with Python 3.11+.
- [x] Missing FFmpeg produces a readable Portuguese message.
- [x] No server/database/login is required.

## Gate B — JSON

- [x] Minimal transformative JSON validates.
- [x] Full future JSON validates even with currently ignored future fields.
- [x] Invalid path error names exact field, e.g. `shorts[0].timeline[1].end`.
- [x] Defaults inherit into Short and segment overrides win.

## Gate C — timeline

Using one real source video:

- [x] A Short with 3 source segments renders in the requested order.
- [x] Exact source time ranges are respected within practical FFmpeg tolerance.
- [x] Final output is one continuous MP4.

## Gate D — transformation layer

- [x] Segment 1 has generated voiceover.
- [x] Segment 2 can keep original audio without voiceover.
- [x] Segment 3 has generated voiceover.
- [x] Source audio ducks under each voiceover.
- [x] Narration is not truncated silently.
- [x] Narration captions appear and are readable.
- [x] Hook text appears at the beginning.

## Gate E — video output

- [x] 1080x1920.
- [x] H.264 + AAC.
- [x] No black bars with default center crop.
- [x] UTF-8 Portuguese text renders correctly.
- [x] Output plays in standard Windows player/browser.

## Gate F — multiple Shorts

- [x] One JSON containing 2+ Shorts renders them sequentially.
- [x] One Short failure does not corrupt already completed outputs.
- [x] Output names are unique and Windows-safe.

## Gate G — UX

- [x] GUI remains responsive.
- [x] Progress stage updates.
- [x] Cancel stops future work and best-effort terminates active process.
- [x] Open Output Folder works.

## Gate H — transformative heuristic

- [x] Plan with no narration triggers warning but can still render.
- [x] Warning explicitly says it is not an official monetization decision.

## Gate I — tests/docs

- [x] pytest green.
- [x] README contains install/run instructions.
- [x] README includes FFmpeg setup.
- [x] README explains SAPI voice dependency/fallback.
- [x] Example JSON included.

## PASS definition

The MVP is PASS only if a user can select one episode, paste a JSON containing a multi-clip commentary Short, click Generate, and receive a final vertical video with original narration, captions, source-audio ducking, hook, and multiple cuts **without opening CapCut afterward**.

## M3.4 — validação técnica em 04/10/2026

- [x] 61 testes anteriores + 29 novos: 90 PASS.
- [x] JSON antigo continua renderizando com o caminho anterior.
- [x] Punch-in, slow zoom, freeze pós-crop, text card, fade e marcador.
- [x] Speed change 0.75–1.35; pitch preservado por atempo, FFT 440 Hz validada.
- [x] Freeze continue/duck/mute; captions continuam independentes.
- [x] Micro trim limitado a bordas pretas/PCM zero; fallback seguro.
- [x] Nenhuma remoção de fala/reação no smoke real.
- [x] Pace/warnings opcionais e crossfade curto testados.
- [x] Comparação real before/cinematic gerada, 1080×1920 H.264/AAC.
- [x] Faber, ducking, anime tracking, captions premium e branding preservados.
- [x] Sem API nova ou feature M4+.
- [ ] Aprovação humana específica de ritmo/naturalidade dos novos MP4s.

Evidências e limitações: `M3_4_REPORT.md`.
