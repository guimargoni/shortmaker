"""Opt-in editorial composition; old plans take the unchanged render path."""
import logging
from .editing_models import Effect, TrimPolicy, Editing
from .audio import tempo_filters
from .ffmpeg_runner import Cancelled


PACE = {
    'dramatic': {'punch_in': .65, 'slow_zoom': 5, 'trim_cap_ms': 250},
    'normal': {'punch_in': .5, 'slow_zoom': 4, 'trim_cap_ms': 450},
    'fast': {'punch_in': .4, 'slow_zoom': 3, 'trim_cap_ms': 650},
}


def effect_duration(effect, pace='normal'):
    if effect.duration is not None:
        return effect.duration
    return {'punch_in': PACE[pace]['punch_in'], 'freeze_frame': .8, 'text_card': 1.2, 'fade': .2}.get(effect.type, 0)


def speed_parts(segment):
    length = (segment.end-segment.start)/segment.speed
    changes = sorted((e for e in segment.effects if e.type == 'speed_change'), key=lambda e: e.start_at)
    parts, cursor = [], 0
    for effect in changes:
        if effect.start_at < cursor or effect.end_at > length:
            raise ValueError('speed_change sobreposto ou fora da duração visual base')
        if effect.start_at > cursor:
            parts.append((cursor, effect.start_at, 1, 'continue'))
        parts.append((effect.start_at, effect.end_at, effect.speed, effect.audio_mode))
        cursor = effect.end_at
    if cursor < length:
        parts.append((cursor, length, 1, 'continue'))
    return parts


def edited_visual(segment):
    return sum((b-a)/speed for a,b,speed,_ in speed_parts(segment))


def validate_effects(segment, pace='normal'):
    length = edited_visual(segment)
    intervals = []
    for e in segment.effects:
        if e.type == 'slow_zoom' and e.end_at is None:
            e.end_at = min(length, e.start_at + PACE[pace]['slow_zoom'])
        if e.type == 'speed_change':
            continue
        start = e.start_at if e.type == 'slow_zoom' else e.at
        end = e.end_at if e.type == 'slow_zoom' else start + effect_duration(e, pace)
        if start >= length or end > length + 1e-6:
            raise ValueError(f'{e.type}: evento fora da duração visual ({length:.3f}s)')
        if e.type in {'punch_in','slow_zoom'}:
            if any(start < b and end > a for a,b in intervals):
                raise ValueError('zooms sobrepostos: escolha um foco editorial por intervalo')
            intervals.append((start,end))
    return length


def prepare_clip(source, segment, temp, index, runner, ffmpeg, media, pace):
    """Speed changes alter source timing, never the separately synthesized voice.

    Freeze replaces video within its interval; audio clock and total length hold.
    Lossless intermediate avoids an extra lossy encode before the existing crop.
    """
    freezes = [e for e in segment.effects if e.type == 'freeze_frame']
    changes = [e for e in segment.effects if e.type == 'speed_change']
    if segment.trim_policy.remove_dead_time:
        segment = trim_blank_edges(source, segment, temp, index, runner, ffmpeg, media, pace)
    if not changes and not (media.audio and any(e.audio_mode != 'continue' for e in freezes)):
        return source, segment
    graph, pairs = [], []
    parts = speed_parts(segment)
    for j,(a,b,speed,mode) in enumerate(parts):
        rate = segment.speed*speed
        graph.append(f'[0:v]trim=start={a*segment.speed}:end={b*segment.speed},setpts=(PTS-STARTPTS)/{rate}[v{j}]')
        if media.audio:
            volume = ',volume=0' if mode == 'mute' else ',volume=0.158489' if mode == 'duck' else ''
            graph.append(f'[0:a]atrim=start={a*segment.speed}:end={b*segment.speed},asetpts=PTS-STARTPTS,{tempo_filters(rate)}{volume},apad,atrim=duration={(b-a)/speed}[a{j}]')
            pairs.append(f'[v{j}][a{j}]')
        else:
            pairs.append(f'[v{j}]')
    graph.append(''.join(pairs)+f'concat=n={len(parts)}:v=1:a={1 if media.audio else 0}[base]'+('[audio]' if media.audio else ''))
    fps = media.fps
    graph.append(f'[base]fps={fps}[clock]')
    graph.append('[clock]null[v]')
    if media.audio:
        current_audio = 'audio'
        for j,e in enumerate(freezes):
            if e.audio_mode != 'continue':
                gain = 0 if e.audio_mode == 'mute' else .158489
                graph.append(f"[{current_audio}]volume={gain}:enable='between(t,{e.at},{e.at+effect_duration(e,pace)})'[fAudio{j}]")
                current_audio = f'fAudio{j}'
        graph.append(f'[{current_audio}]anull[a]')
    graph_path = temp/f'editing-{index}.txt'
    graph_path.write_text(';'.join(graph),encoding='utf-8')
    destination = temp/f'edited-{index}.mkv'
    args = [ffmpeg,'-y','-v','error','-ss',segment.start,'-t',segment.end-segment.start,'-i',source,'-/filter_complex',graph_path.name,'-map','[v]']
    if media.audio:
        args += ['-map','[a]','-c:a','pcm_s16le']
    runner.run(args+['-c:v','ffv1','-t',edited_visual(segment),destination],cwd=temp)
    return destination, segment.model_copy(update={'start':0.,'end':edited_visual(segment),'speed':1.,'effects':[]})


def video_graph(vf, effects, fps, pace):
    freezes = sorted((e for e in effects if e.type == 'freeze_frame'), key=lambda e:e.at)
    if not freezes:
        return f'[0:v:0]{vf}[v]'
    before,after = vf.split(',ass=',1)
    graph = [f'[0:v:0]{before}[editBase]']
    current = 'editBase'
    for j,e in enumerate(freezes):
        first = round(e.at*fps)
        last = max(first,round((e.at+effect_duration(e,pace))*fps)-1)
        graph += [f'[{current}]split=2[freezeA{j}][freezeB{j}]', f'[freezeA{j}][freezeB{j}]freezeframes=first={first}:last={last}:replace={first}[frozen{j}]']
        current = f'frozen{j}'
    graph.append(f'[{current}]ass={after}[v]')
    return ';'.join(graph)


def trim_blank_edges(source, segment, temp, index, runner, ffmpeg, media, pace):
    """Only editor-authorized blank edges with exactly zero decoded PCM samples.

    Silent character reactions are never candidates. Preservation is the default;
    no cuts when narration/effects/time marks might become inconsistent.
    """
    policy = segment.trim_policy
    if policy.preserve_reaction or segment.effects or segment.reframe.keyframes or segment.voiceover.enabled or not media.audio:
        logging.info('trim_policy: fallback sem corte (reação preservada, timeline marcada, narração ou áudio ausente)')
        return segment
    try:
        import cv2
    except ImportError:
        logging.warning('trim_policy: OpenCV indisponível, fallback sem corte')
        return segment
    import wave
    cap_ms = policy.max_removal_ms if 'max_removal_ms' in policy.model_fields_set else PACE[pace]['trim_cap_ms']
    capture = cv2.VideoCapture(str(source))
    try:
        fps = capture.get(cv2.CAP_PROP_FPS)
        if not capture.isOpened() or not fps:
            return segment
        frame_count = int(min(cap_ms/1000, (segment.end-segment.start)/4)*fps)
        trims = []
        for edge in ('start','end'):
            count = 0
            for frame in range(frame_count):
                runner.check()
                at = segment.start+frame/fps if edge == 'start' else segment.end-(frame+1)/fps
                capture.set(cv2.CAP_PROP_POS_MSEC,at*1000)
                ok, picture = capture.read()
                if not ok or picture.max() > 2:
                    break
                count += 1
            length = count/fps
            if not length:
                trims.append(0)
                continue
            at = segment.start if edge == 'start' else segment.end-length
            wav = temp/f'trim-{index}-{edge}.wav'
            runner.run([ffmpeg,'-y','-v','error','-ss',at,'-t',length,'-i',source,'-vn','-c:a','pcm_s16le',wav])
            with wave.open(str(wav),'rb') as audio:
                samples = audio.readframes(audio.getnframes())
            trims.append(length if samples and not any(samples) else 0)
        logging.info('trim_policy: bordas pretas com PCM zero, remoção inicial=%.3fs final=%.3fs; limite=%sms',*trims,cap_ms)
        return segment.model_copy(update={'start':segment.start+trims[0],'end':segment.end-trims[1]})
    except Cancelled:
        raise
    except Exception as exc:
        logging.warning('trim_policy: análise inconclusiva, fallback sem corte: %s', exc)
        return segment
    finally:
        capture.release()


def montage_crossfade(files, durations, short, temp, runner, ffmpeg):
    transitions = [s.transition_out if s.transition_out else short.model_dump().get('transition',{}) for s in short.timeline[:-1]]
    if not any(t.get('type') == 'crossfade' for t in transitions):
        return None
    graph, args = [], [ffmpeg,'-y','-v','error']
    for i,path in enumerate(files):
        args += ['-i',path]
        graph += [f'[{i}:v]settb=AVTB,setpts=PTS-STARTPTS[v{i}]',f'[{i}:a]asetpts=PTS-STARTPTS[a{i}]']
    total, video, audio = durations[0], 'v0', 'a0'
    for i,t in enumerate(transitions,1):
        cross = t.get('type') == 'crossfade'
        overlap = t.get('duration',.12) if cross else 0
        if overlap > .25 or overlap >= min(durations[i-1],durations[i])/2:
            raise ValueError('crossfade deve ser <=0.25s e menor que metade dos clips adjacentes')
        if cross:
            graph += [f'[{video}][v{i}]xfade=transition=fade:duration={overlap}:offset={total-overlap}[mv{i}]',f'[{audio}][a{i}]acrossfade=d={overlap}:c1=tri:c2=tri[ma{i}]']
        else:
            graph += [f'[{video}][{audio}][v{i}][a{i}]concat=n=2:v=1:a=1[mv{i}][ma{i}]']
        video,audio = f'mv{i}',f'ma{i}'
        total += durations[i]-overlap
    path = temp/'crossfade.txt'
    path.write_text(';'.join(graph),encoding='utf-8')
    runner.run(args+['-/filter_complex',path.name,'-map',f'[{video}]','-map',f'[{audio}]','-c:v','libx264','-preset',short.video['preset'],'-crf',short.video['crf'],'-pix_fmt','yuv420p','-c:a','aac','-ar',48000,'-ac',2,temp/'montage.mp4'],cwd=temp)
    return total


def visual_filters(effects, fps, pace='normal'):
    filters, zoom, punches = [], [], []
    for e in effects:
        if e.type == 'punch_in':
            duration = effect_duration(e,pace)
            u = f'clip((in/{fps}-{e.at})/{duration},0,1)'
            punches.append((e.scale, f'pow(sin(PI*{u}),2)'))
        elif e.type == 'slow_zoom':
            u = f'clip((in/{fps}-{e.start_at})/{e.end_at-e.start_at},0,1)'
            smooth = f'({u})*({u})*(3-2*({u}))'
            zoom.append(f'({e.from_scale-1})*gte(in/{fps},{e.start_at})+({e.to_scale-e.from_scale})*({smooth})')
        elif e.type == 'fade':
            filters.append(f'fade=t={e.direction}:st={e.at}:d={effect_duration(e,pace)}')
    if zoom or punches:
        baseline = '1'+('+'+'+'.join(zoom) if zoom else '')
        target = baseline
        for scale,pulse in punches:
            target = f'({target})+({scale}-({baseline}))*({pulse})'
        filters.insert(0,f"zoompan=z='min(1.25,{target})':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps={fps}")
    return ','.join(filters)


def add_text_cards(ass, effects, pace='normal'):
    for i,e in enumerate(effects):
        if e.type != 'text_card':
            continue
        from .ass_builder import wrap_overlay
        styles = {'editorial': (42,'#FFFFFF'), 'impact': (48,'#FFD84D'), 'subtle': (36,'#FFFFFF')}
        size, foreground = styles[e.style]
        ass.add([(e.at,e.at+effect_duration(e,pace),wrap_overlay(e.text,32))],f'Card{i}',{'position':'top','margin_top':285,'style':{'font_size':size,'font_color':foreground,'outline_width':3,'background_enabled':e.background}},size)


def quality_warnings(short):
    if not short.editing.get('editorial_quality_warnings'):
        return []
    messages, times, freezes = [], [], 0
    durations = [edited_visual(s) for s in short.timeline]
    offset = 0
    for s,duration in zip(short.timeline,durations):
        if duration > 12 and not s.voiceover.enabled and not any(e.type != 'hard_cut_marker' for e in s.effects):
            messages.append('trecho contínuo >12s sem comentário/mudança editorial')
        for e in s.effects:
            if e.type == 'hard_cut_marker':
                continue
            times.append(offset+(e.start_at if e.type in {'slow_zoom','speed_change'} else e.at))
            freezes += e.type == 'freeze_frame'
            if e.type == 'punch_in' and e.scale > 1.15 or e.type == 'slow_zoom' and max(e.from_scale,e.to_scale) > 1.15:
                messages.append('zoom acima de 1.15')
            if e.type == 'text_card' and effect_duration(e) > 2:
                messages.append('text card acima de 2s')
        offset += duration
    times.sort()
    if any(times[i+3]-times[i] <= 5 for i in range(len(times)-3)):
        messages.append('mais de 3 efeitos em 5s')
    if freezes > 2:
        messages.append('mais de 2 freeze frames')
    if max(durations)/sum(durations) >= .7:
        messages.append('70%+ formado por um único clip contínuo')
    return [f'{short.id}: Aviso de qualidade editorial: {m}' for m in dict.fromkeys(messages)]
