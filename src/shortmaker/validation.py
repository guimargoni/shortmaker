from copy import deepcopy
import json
from pydantic import ValidationError
from .constants import DEFAULTS
from .models import Plan


def deep_merge(base, override):
    result = deepcopy(base)
    for key, value in override.items():
        result[key] = deep_merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else deepcopy(value)
    return result


def field_path(loc):
    return "".join(f"[{p}]" if isinstance(p, int) else ("." if i else "") + str(p) for i, p in enumerate(loc))


def parse_plan(text):
    try:
        data = json.loads(text) if isinstance(text, str) else deepcopy(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido na linha {exc.lineno}, coluna {exc.colno}: {exc.msg}") from exc
    try:
        # Validate structure before inheritance so malformed dictionaries have readable paths.
        Plan.model_validate(data)
        defaults = deep_merge(DEFAULTS, data.get("defaults", {}))
        from .settings import SETTINGS
        for key, model in SETTINGS.items():
            try:
                defaults[key] = model.model_validate(defaults.get(key, {})).model_dump()
            except ValidationError as exc:
                raise ValueError("\n".join(f"defaults.{key}{'.' if e['loc'] else ''}{field_path(e['loc'])}: {e['msg']}" for e in exc.errors())) from exc
        for i, short in enumerate(data["shorts"]):
            inherited = deep_merge(defaults, {k: v for k, v in short.items() if k in DEFAULTS})
            for key, model in SETTINGS.items():
                try:
                    inherited[key] = model.model_validate(inherited.get(key, {})).model_dump()
                except ValidationError as exc:
                    raise ValueError("\n".join(f"shorts[{i}].{key}{'.' if e['loc'] else ''}{field_path(e['loc'])}: {e['msg']}" for e in exc.errors())) from exc
            short.update(inherited)
            for segment in short["timeline"]:
                segment["reframe"] = deep_merge(inherited["video"].get("reframe", {}), segment.get("reframe", {}))
                segment["source_audio"] = deep_merge(inherited["audio"].get("source_audio", {}), segment.get("source_audio", {}))
                segment["voiceover"] = deep_merge(inherited["voice"], segment.get("voiceover", {}))
                segment["captions"] = deep_merge(inherited["captions"], segment.get("captions", {}))
        plan = Plan.model_validate(data)
    except ValidationError as exc:
        raise ValueError("\n".join(f"{field_path(e['loc'])}: {e['msg']}" for e in exc.errors())) from exc
    validate_settings(plan)
    return plan


def validate_settings(plan):
    from .settings import SETTINGS, Captions, Transition
    for i, short in enumerate(plan.shorts):
        def validate(model, value, prefix):
            try:
                return model.model_validate(value).model_dump()
            except ValidationError as exc:
                raise ValueError("\n".join(f"{prefix}{'.' if e['loc'] else ''}{field_path(e['loc'])}: {e['msg']}" for e in exc.errors())) from exc
        for key, model in SETTINGS.items():
            validate(model, short.model_dump().get(key, {}), f"shorts[{i}].{key}")
        for j, segment in enumerate(short.timeline):
            from .editing import validate_effects
            validate_effects(segment, short.editing.get("pace", "normal"))
            segment.captions = validate(Captions, segment.captions, f"shorts[{i}].timeline[{j}].captions")
            for key in ("transition_in", "transition_out"):
                if getattr(segment, key):
                    setattr(segment, key, validate(Transition, getattr(segment, key), f"shorts[{i}].timeline[{j}].{key}"))
                    if getattr(segment, key).get("type") == "crossfade" and getattr(segment, key)["duration"] > .25:
                        raise ValueError(f"shorts[{i}].timeline[{j}].{key}: crossfade máximo 0.25s")
            if segment.voiceover.enabled and segment.voiceover.engine not in {"sapi", "piper"}:
                raise ValueError(f"shorts[{i}].timeline[{j}].voiceover.engine: use piper ou sapi")


def editorial_warnings(plan):
    result = []
    for short in plan.shorts:
        if not short.enabled or not short.transformative_gate.get("enabled", True):
            continue
        gate = short.transformative_gate
        words = sum(len(s.voiceover.text.split()) for s in short.timeline if s.voiceover.enabled)
        long_clip = any((s.end - s.start) / s.speed > gate.get("warn_continuous_source_clip_over_seconds", 25) and not s.voiceover.enabled for s in short.timeline)
        if (not words and gate.get("warn_if_no_voiceover", True)) or words < gate.get("warn_if_original_words_below", 20) or long_clip:
            result.append(f"{short.id}: Aviso editorial: este plano parece ter pouca contribuição original. Isso não impede a renderização e não é uma avaliação oficial de monetização.")
    return result
