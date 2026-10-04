def segment_duration(segment, narration=0):
    visual = (segment.end - segment.start) / segment.speed
    total = max(visual, narration + segment.voiceover.start_offset) if narration else visual
    overflow = total - visual
    if overflow > 1.5 + 1e-6:
        raise ValueError(f"Narração excede o segmento em {overflow:.2f}s (máximo 1.5s). Aumente end, reduza text ou aumente voiceover.rate.")
    return total, overflow


def validate_ranges(short, media, index):
    for j, segment in enumerate(short.timeline):
        if segment.end > media.duration + .001:
            raise ValueError(f"shorts[{index}].timeline[{j}].end: {segment.end:.3f}s excede a duração da fonte ({media.duration:.3f}s)")
