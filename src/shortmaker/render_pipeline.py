import json
import logging
from pathlib import Path
import tempfile
from .ass_builder import AssBuilder, wrap_overlay
from .audio import source_volume, tempo_filters
from .captions import narration_events, transcribe
from .ffmpeg_runner import Runner, Cancelled
from .media_probe import probe
from .output_naming import output_path
from .paths import executable, writable_output
from .timeline import segment_duration, validate_ranges
from .tts import synthesize
from .validation import editorial_warnings
from .reframe import analyze_anime, crop_filter
from .branding import add_end_tag
from .editing import prepare_clip, visual_filters, add_text_cards, quality_warnings, montage_crossfade, video_graph


class Pipeline:
    def __init__(self, cancel=None, progress=None):
        self.runner = Runner(cancel)
        self.progress = progress or (lambda stage, pct, message: None)

    def emit(self, stage, pct, message):
        logging.info("%s: %s", stage, message)
        self.progress(stage, pct, message)

    def render(self, source, plan, folder):
        source = Path(source).resolve()
        if not source.is_file():
            raise ValueError("Vídeo fonte não encontrado")
        self.emit("validating", 0, "Validando dependências e saída")
        self.ffmpeg = executable("ffmpeg")
        executable("ffprobe")
        folder = writable_output(folder)
        for warning in editorial_warnings(plan):
            self.emit("validating", 0, warning)
        for short in plan.shorts:
            for warning in quality_warnings(short):
                self.emit("validating", 0, warning)
        self.emit("probing", 0, "Inspecionando vídeo fonte")
        media = probe(source, self.runner)
        enabled = [(i, s) for i, s in enumerate(plan.shorts) if s.enabled]
        outputs, failures = [], []
        for position, (index, short) in enumerate(enabled):
            self.runner.check()
            self.base = position / max(1, len(enabled)) * 100
            self.span = 100 / max(1, len(enabled))
            try:
                validate_ranges(short, media, index)
                destination = output_path(folder, short, index + 1)
                with tempfile.TemporaryDirectory(prefix="shortmaker-", dir=folder) as temp:
                    temp = Path(temp)
                    reframe_report = self.short_render(source, plan, short, media, temp)
                    self.runner.check()
                    # Windows rename refuses collisions, preserving existing output.
                    (temp / "final.mp4").rename(destination)
                    outputs.append(destination)
                    if short.export.get("write_metadata_sidecar", True):
                        destination.with_suffix(".metadata.json").write_text(json.dumps({"schema_version": plan.schema_version,
                            "project": plan.project, "short": short.model_dump(), "publishing": plan.publishing,
                            "reframe_report": reframe_report, "editing_report": self.editing_report}, ensure_ascii=False, indent=2), encoding="utf-8")
                self.emit("completed", self.base + self.span, f"Short {position + 1}/{len(enabled)} concluído: {destination.name}")
            except Cancelled:
                self.emit("cancelled", self.base, "Cancelado; arquivos já concluídos foram preservados")
                raise
            except Exception as exc:
                logging.exception("Falha no Short %s", short.id)
                failures.append(f"{short.id}: {exc}")
                self.emit("failed", self.base + self.span, failures[-1])
        return outputs, failures

    def short_render(self, source, plan, short, media, temp):
        fps = media.fps if short.video.get("fps_mode", "source") == "source" else short.video.get("fps", 30)
        files, durations = [], []
        reframe_report = []
        self.editing_report = []
        pace = short.editing.get("pace", "normal")
        for i, segment in enumerate(short.timeline):
            self.runner.check()
            pct = self.base + self.span * (.8 * i / len(short.timeline))
            label = f"{short.id} — segmento {i + 1}/{len(short.timeline)}"
            self.emit("preparing_segment", pct, label)
            effects = segment.effects
            original_segment = segment
            clip_source, segment = prepare_clip(source, segment, temp, i, self.runner, self.ffmpeg, media, pace)
            if effects or original_segment.trim_policy.remove_dead_time:
                self.editing_report.append({"segment": i, "effects": [e.model_dump() for e in effects],
                    "source_start": original_segment.start, "source_end": original_segment.end,
                    "trim_start_seconds": max(0, segment.start-original_segment.start) if clip_source == source else 0,
                    "trim_end_seconds": max(0, original_segment.end-segment.end) if clip_source == source else 0,
                    "prepared_visual_duration": (segment.end-segment.start)/segment.speed})
            voice_duration = 0
            wav = temp / f"voice-{i}.wav"
            if segment.voiceover.enabled:
                self.emit("generating_voiceover", pct, label + " — gerando narração")
                voice_duration = synthesize(segment.voiceover, wav, self.runner)
            try:
                duration, overflow = segment_duration(segment, voice_duration)
            except ValueError as exc:
                raise ValueError(f"timeline[{i}].voiceover: {exc}") from exc
            durations.append(duration)
            ass = AssBuilder()
            captions = segment.captions
            self.emit("generating_captions", pct, label + " — legendas")
            if captions["enabled"]:
                if voice_duration and captions.get("mode") in {"narration", "both"}:
                    ass.add(narration_events(segment.voiceover.text, voice_duration, segment.voiceover.start_offset,
                                            captions["max_chars_per_line"], captions["max_lines"]), "Narration", captions)
                if not voice_duration and (captions.get("source_dialogue") or captions.get("mode") in {"source", "source_dialogue", "both"}):
                    if not media.audio:
                        raise ValueError(f"timeline[{i}].captions: fonte não contém áudio para transcrever")
                    audio = temp / f"dialogue-{i}.wav"
                    self.runner.run([self.ffmpeg, "-y", "-v", "error", "-ss", segment.start, "-t", segment.end - segment.start,
                                     "-i", clip_source, "-vn", "-af", tempo_filters(segment.speed), "-ar", 16000, "-ac", 1, audio])
                    events = transcribe(audio, temp / f"transcript-{i}.json", captions, plan.project.get("source_language"), self.runner)
                    ass.add(events, "Dialogue", captions)
            if segment.overlay_text:
                overlay = segment.overlay_text
                settings = overlay if isinstance(overlay, dict) else {"position": "center"}
                text = overlay.get("text", "") if isinstance(overlay, dict) else overlay
                start = float(settings.get("start", 0))
                ass.add([(start, min(duration, float(settings.get("end", duration))), wrap_overlay(text))], "Overlay", settings)
            add_text_cards(ass, effects, pace)
            ass_file = temp / f"segment-{i}.ass"
            ass.write(ass_file)
            target = temp / f"segment-{i}.mp4"
            files.append(target)
            reframe = segment.reframe
            mode = reframe.mode
            if mode not in {"center_crop", "manual", "anime_face_track", "manual_keyframes"}:
                if reframe.strict:
                    raise ValueError(f"timeline[{i}].reframe.mode: {mode} ainda não implementado em modo strict")
                self.emit("preparing_segment", pct, f"Aviso: {mode} usa center_crop")
                mode = "center_crop"
            width, height = round(1080 * reframe.zoom / 2) * 2, round(1920 * reframe.zoom / 2) * 2
            x = reframe.manual_x if mode == "manual" and reframe.manual_x is not None else .5
            y = reframe.manual_y if mode == "manual" and reframe.manual_y is not None else .5
            visual = (segment.end - segment.start) / segment.speed
            crop = f"crop=1080:1920:(iw-1080)*{x}:(ih-1920)*{y}"
            if mode == "anime_face_track":
                points, stats = analyze_anime(clip_source, segment, temp, i, self.runner, self.ffmpeg)
                reframe_report.append({"segment": i, **stats})
                crop = crop_filter(points)
                self.emit("preparing_segment", pct, f"Anime: {stats['frames_with_faces']}/{stats['sampled_frames']} amostras com rosto; fallback={stats['fallback']}")
            elif mode == "manual_keyframes":
                if any(k.at > visual for k in reframe.keyframes):
                    raise ValueError(f"timeline[{i}].reframe.keyframes: at excede duração visual ({visual:.3f}s)")
                crop = crop_filter([(k.at, k.x, k.y) for k in reframe.keyframes])
            vf = f"setpts=(PTS-STARTPTS)/{segment.speed},scale={width}:{height}:force_original_aspect_ratio=increase,{crop},setsar=1,fps={fps}"
            effect_filters = visual_filters(effects, fps, pace)
            if effect_filters:
                vf += "," + effect_filters
            vf += f",tpad=stop_mode=clone:stop_duration={overflow},ass={ass_file.name}"
            for edge, transition in (("in", segment.transition_in), ("out", segment.transition_out)):
                transition = transition or short.model_dump().get("transition", {})
                if transition.get("type") == "fade":
                    fade = min(float(transition.get("duration", .15)), duration / 2)
                    vf += f",fade=t={edge}:st={0 if edge == 'in' else duration-fade}:d={fade}"
            args = [self.ffmpeg, "-y", "-v", "error", "-ss", segment.start, "-t", segment.end - segment.start, "-i", clip_source]
            if media.audio:
                audio_filter = f"[0:a:0]asetpts=PTS-STARTPTS,{tempo_filters(segment.speed)},{source_volume(segment, voice_duration)},apad,atrim=duration={duration}[src]"
                next_input = 1
            else:
                args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
                audio_filter = f"[1:a]atrim=duration={duration}[src]"
                next_input = 2
            if voice_duration:
                args += ["-i", wav]
                audio_filter += f";[{next_input}:a]adelay={round(segment.voiceover.start_offset*1000)}:all=1,apad,atrim=duration={duration}[voice];[src][voice]amix=inputs=2:duration=longest:normalize=0[a]"
            else:
                audio_filter += ";[src]anull[a]"
            graph = video_graph(vf, effects, fps, pace) + ";" + audio_filter
            if mode in {"anime_face_track", "manual_keyframes"} or effects:
                graph_file = temp / f"graph-{i}.txt"
                graph_file.write_text(graph, encoding="utf-8")
                graph_args = ["-/filter_complex", graph_file.name]
            else:
                graph_args = ["-filter_complex", graph]
            self.emit("rendering_segment", pct, label + " — renderizando")
            self.runner.run(args + graph_args + ["-map", "[v]", "-map", "[a]", "-t", duration,
                                   "-c:v", "libx264", "-preset", short.video["preset"], "-crf", short.video["crf"],
                                   "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", short.export["audio_bitrate"], "-ar", 48000, "-ac", 2, target], cwd=temp)
        self.emit("concatenating", self.base + self.span * .82, short.id + " — concatenando")
        concat = temp / "concat.txt"
        concat.write_text("\n".join(f"file '{p.name}'" for p in files), encoding="utf-8")
        total = montage_crossfade(files, durations, short, temp, self.runner, self.ffmpeg)
        if total is None:
            self.runner.run([self.ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", 0, "-i", concat.name,
                             "-c", "copy", "montage.mp4"], cwd=temp)
            total = sum(durations)
        global_ass = AssBuilder()
        if short.hook["enabled"] and short.editorial.get("hook_text"):
            global_ass.add([(0, min(total, short.hook["duration"]), wrap_overlay(short.editorial["hook_text"], 26))], "Hook", short.hook, 76)
        label = short.editorial.get("source_label_text") or plan.project.get("source_name")
        if short.source_label["enabled"] and label:
            label_settings = dict(short.source_label)
            if short.branding.get("end_tag", {}).get("enabled") and label_settings.get("position") == "bottom":
                label_settings["margin_bottom"] = max(145, label_settings.get("margin_bottom", 90))
            global_ass.add([(max(0, total - short.source_label["show_last_seconds"]), total, wrap_overlay(label, 45))], "Source", label_settings, 38)
        add_end_tag(global_ass, total, short.branding.get("end_tag", {}))
        global_ass.write(temp / "global.ass")
        args = [self.ffmpeg, "-y", "-v", "error", "-i", "montage.mp4", "-map", "0:v:0", "-map", "0:a:0"]
        if global_ass.events:
            args += ["-vf", "ass=global.ass", "-c:v", "libx264", "-preset", short.video["preset"], "-crf", short.video["crf"], "-pix_fmt", "yuv420p"]
        else:
            args += ["-c:v", "copy"]
        self.emit("normalizing_audio", self.base + self.span * .9, short.id + " — normalizando áudio")
        if short.audio["normalize"] and (media.audio or any(segment.voiceover.enabled for segment in short.timeline)):
            args += ["-af", f"loudnorm=I={short.audio['target_lufs']}:TP={short.audio['true_peak']}:LRA=11"]
        args += ["-c:a", "aac", "-b:a", short.export["audio_bitrate"], "-ar", 48000, "-ac", 2]
        if short.export.get("faststart", True):
            args += ["-movflags", "+faststart"]
        self.runner.run(args + ["final.mp4"], cwd=temp)
        self.emit("finalizing", self.base + self.span * .98, short.id + " — salvando MP4")
        return reframe_report
