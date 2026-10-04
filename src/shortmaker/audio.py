def tempo_filters(speed):
    filters = []
    while speed > 2:
        filters.append("atempo=2")
        speed /= 2
    while speed < .5:
        filters.append("atempo=0.5")
        speed *= 2
    filters.append(f"atempo={speed:.8f}")
    return ",".join(filters)


def source_volume(segment, voice_duration):
    if segment.source_audio.mode == "mute":
        return "volume=0"
    if segment.source_audio.mode == "keep":
        return "volume=1"
    db = segment.voiceover.duck_source_db
    if db is None:
        db = segment.source_audio.duck_db
    gain = 10 ** (db / 20)
    if voice_duration:
        start = segment.voiceover.start_offset
        return f"volume={gain}:enable='between(t,{start},{start + voice_duration})'"
    return f"volume={gain}"
