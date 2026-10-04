# SHORTMAKER JSON CONTRACT v1.1

## Core principle

The JSON must describe **editorial intent + deterministic execution instructions**. It is intentionally more robust than the current renderer so future features do not require breaking the contract.

## Top-level structure

```json
{
  "schema_version": "1.1",
  "project": {},
  "defaults": {},
  "shorts": [],
  "publishing": {},
  "compatibility": {}
}
```

## Minimal transformative plan

```json
{
  "schema_version": "1.1",
  "project": {
    "id": "example-project",
    "title": "Example source",
    "source_name": "Example — Episode 1",
    "source_language": "ja",
    "output_language": "pt-BR"
  },
  "shorts": [
    {
      "id": "short-01",
      "editorial": {
        "content_mode": "commentary",
        "title": "Exemplo",
        "hook_text": "Foi aqui que tudo mudou."
      },
      "timeline": [
        {
          "type": "source_clip",
          "start": "00:01:00.000",
          "end": "00:01:06.000",
          "voiceover": {
            "enabled": true,
            "text": "Esse começo cria uma sensação de segurança que dura muito pouco."
          }
        },
        {
          "type": "source_clip",
          "start": "00:02:10.000",
          "end": "00:02:17.000",
          "source_audio": {"mode": "keep"}
        },
        {
          "type": "source_clip",
          "start": "00:03:20.000",
          "end": "00:03:27.000",
          "voiceover": {
            "enabled": true,
            "text": "E é aqui que a história muda completamente de tom."
          }
        }
      ]
    }
  ]
}
```

## Full future-oriented structure

```json
{
  "schema_version": "1.1",
  "project": {
    "id": "aot-s01e01",
    "title": "Attack on Titan S01E01",
    "source_name": "Attack on Titan — S1E1",
    "source_language": "ja",
    "output_language": "pt-BR",
    "notes": "Editorial plan generated externally."
  },
  "defaults": {
    "video": {
      "width": 1080,
      "height": 1920,
      "aspect_ratio": "9:16",
      "fps_mode": "source",
      "video_codec": "libx264",
      "preset": "medium",
      "crf": 20,
      "pixel_format": "yuv420p",
      "reframe": {
        "mode": "center_crop",
        "strict": false,
        "zoom": 1.0,
        "manual_x": null,
        "manual_y": null
      }
    },
    "audio": {
      "normalize": true,
      "target_lufs": -16,
      "true_peak": -1.5,
      "source_audio": {
        "mode": "duck",
        "duck_db": -16
      }
    },
    "voice": {
      "engine": "sapi",
      "voice": null,
      "rate": 1.0,
      "volume": 1.0
    },
    "captions": {
      "enabled": true,
      "mode": "narration",
      "source_dialogue": false,
      "whisper_model": "small",
      "max_lines": 2,
      "max_chars_per_line": 34,
      "position": "bottom",
      "margin_bottom": 230,
      "style": {
        "font_family": "Arial",
        "font_size": 64,
        "font_weight": "bold",
        "font_color": "#FFFFFF",
        "outline_color": "#000000",
        "outline_width": 4,
        "background_enabled": false
      }
    },
    "hook": {
      "enabled": true,
      "duration": 2.2,
      "position": "top",
      "margin_top": 165,
      "style": {
        "font_family": "Arial",
        "font_size": 76,
        "font_color": "#FFFFFF",
        "outline_color": "#000000",
        "outline_width": 5,
        "max_width_pct": 0.9
      }
    },
    "source_label": {
      "enabled": true,
      "show_last_seconds": 2.0,
      "position": "bottom",
      "margin_bottom": 90
    },
    "transition": {
      "type": "cut",
      "duration": 0.15
    },
    "export": {
      "container": "mp4",
      "audio_codec": "aac",
      "audio_bitrate": "192k",
      "faststart": true,
      "filename_template": "{index:02d}-{slug}-{id}.mp4",
      "write_metadata_sidecar": true
    },
    "transformative_gate": {
      "enabled": true,
      "warn_if_no_voiceover": true,
      "warn_continuous_source_clip_over_seconds": 25,
      "warn_if_original_words_below": 20
    }
  },
  "shorts": [
    {
      "id": "aot-s01e01-01",
      "enabled": true,
      "editorial": {
        "content_mode": "commentary",
        "purpose": "impact",
        "title": "O momento em que tudo mudou",
        "hook_text": "Foi aqui que tudo mudou.",
        "source_label_text": "Attack on Titan — S1E1",
        "cta_text": "Você continuaria assistindo?",
        "notes": ""
      },
      "timeline": [
        {
          "id": "seg-01",
          "type": "source_clip",
          "start": "00:05:42.000",
          "end": "00:05:48.000",
          "speed": 1.0,
          "reframe": {"mode": "center_crop"},
          "source_audio": {"mode": "duck", "duck_db": -16},
          "voiceover": {
            "enabled": true,
            "text": "A série passa o começo inteiro fazendo você acreditar que essas muralhas realmente protegem todo mundo.",
            "engine": "sapi",
            "voice": null,
            "rate": 1.0,
            "volume": 1.0,
            "start_offset": 0.1
          },
          "overlay_text": null,
          "transition_out": {"type": "cut"}
        },
        {
          "id": "seg-02",
          "type": "source_clip",
          "start": "00:05:48.000",
          "end": "00:05:55.000",
          "source_audio": {"mode": "keep"},
          "voiceover": {"enabled": false},
          "transition_out": {"type": "cut"}
        },
        {
          "id": "seg-03",
          "type": "source_clip",
          "start": "00:06:01.000",
          "end": "00:06:09.000",
          "source_audio": {"mode": "duck", "duck_db": -16},
          "voiceover": {
            "enabled": true,
            "text": "E então, em poucos segundos, Attack on Titan destrói essa sensação de segurança.",
            "engine": "sapi",
            "rate": 1.0,
            "volume": 1.0
          }
        }
      ],
      "captions": {
        "enabled": true,
        "mode": "narration"
      },
      "publishing": {
        "approved": false,
        "platforms": {
          "youtube": {
            "enabled": false,
            "privacy": "private",
            "title": "O momento em que tudo mudou",
            "description": "",
            "tags": ["attack on titan", "anime", "shorts"],
            "category_id": null,
            "made_for_kids": false,
            "schedule_at": null
          },
          "tiktok": {"enabled": false},
          "instagram": {"enabled": false}
        }
      }
    }
  ],
  "publishing": {
    "enabled": false,
    "approval_required": true,
    "default_timezone": "America/Sao_Paulo",
    "youtube": {
      "channel_alias": "to-assistindo-isso",
      "schedule_strategy": {
        "mode": "manual",
        "times": ["11:00", "14:00", "18:00", "21:00"],
        "start_date": null,
        "max_per_day": 4
      }
    }
  },
  "compatibility": {
    "allow_unknown_fields": true,
    "minimum_app_version": "0.2.0"
  }
}
```

## Supported MVP values

### `editorial.content_mode`
- commentary
- recommendation
- curiosity
- explainer
- narrative
- review

This value is metadata; rendering is driven by timeline instructions.

### `timeline[].type`
MVP: `source_clip`

Future: `image`, `text_card`, `generated_broll`.

### `source_audio.mode`
- keep
- duck
- mute

### `reframe.mode`
Implement: center_crop, manual
Recognize/fallback: face_track, smart_track

### `transition.type`
Implement: cut
Optional if cheap: fade

### `voiceover.engine`
Required MVP: sapi
Future/optional: edge, piper, user_audio

## Narration overflow rule

If generated narration exceeds visual segment by <= 1.5 seconds, renderer may freeze last frame for the overflow.
If it exceeds by > 1.5 seconds, fail with an actionable error.

## Future publishing fields

Publishing fields are contractual now but ignored for network actions until the YouTube milestone.

## M3.1 — local neural voice extension

Piper is the primary local engine as of M3.1; SAPI remains supported explicitly and
is the automatic local fallback when Piper or its model/configuration is unavailable.
The historical v0.2 examples with explicit `engine: sapi` retain that behavior.

```json
"voice": {
  "engine": "piper",
  "voice_id": "pt_BR-faber-medium",
  "rate": 1.0,
  "volume": 1.0
}
```

Use this object under `defaults` or a Short; `timeline[].voiceover` may override
`engine`, `voice_id`, `rate` and `volume` through the existing deep merge rules.
`voice_id` selects the local `.onnx` and `.onnx.json` pair. Faber is the default;
`pt_BR-cadu-medium` is also tested. `voice` retains its original SAPI voice meaning
and may select the installed fallback voice.

Piper uses `length_scale = 1 / rate` and its synthesis volume control. Actual WAV
duration continues to drive overflow, ducking and caption timing. No renderer
timing, audio or montage rules change. Rendering does not download models or use
any account, remote server, external API or metered service.

## M3.2 — pronunciation and anime reframe

`defaults.voice.pronunciation_overrides` and Short `voice.pronunciation_overrides`
are dictionaries, deep-merged with Short entries winning matching global keys.
Segment `voiceover` overrides use the same inheritance. Whole-word substitutions
apply only to TTS requests: exact case wins, then case-insensitive matching;
punctuation stays intact and replacements are not recursively substituted.
Original text remains in editorial, captions and metadata. Applied overrides are
logged for both Piper and SAPI.

```json
"voice": {"pronunciation_overrides": {"Eren": "Éren", "Mikasa": "Micássa", "Armin": "Ármin"}}
```

New functional reframe modes: `anime_face_track` and `manual_keyframes`.
Anime mode uses the local MIT anime LBP cascade by CPU with automatic center-crop
fallback when detection is unreliable, even with `strict: true`.

```json
"reframe": {
  "mode": "manual_keyframes",
  "keyframes": [{"at": 0.0, "x": 0.35, "y": 0.42}, {"at": 4.5, "x": 0.68, "y": 0.40}]
}
```

For these new keyframes, x/y specify the desired crop **center** in source frame
coordinates, normalized 0–1. `at` is local rendered visual time after `speed`,
before narration overflow freeze. Keyframes must be strictly ordered and within
the segment visual duration; at least one is required for manual mode. Smoothstep
interpolation holds endpoint positions and clamps crop edges to the frame. The
older `manual_x`/`manual_y` keep their existing crop-travel semantics.

## M3.3 — premium captions and channel end tag

Opt-in, backward compatible. Captions inherit from defaults, Short, then segment:

```json
"captions": {
  "style_preset": "premium",
  "highlight_keywords": true,
  "highlight_color": "#FFD84D",
  "keywords": ["Eren", "Mikasa"]
}
```

`keywords` is an explicit editorial list, at most two entries. No automatic
keyword selection. Whole-word case-insensitive matches receive color; punctuation
and original text remain intact. No marked keywords means no highlight. Premium
uses white bold text, black outline and subtle shadow; existing font/size/position
remain configurable. Default preset preserves the previous caption appearance.
No animated words or changes to caption timing, TTS or pronunciation overrides.

`branding` inherits from defaults to Short; disabled by default:

```json
"branding": {
  "end_tag": {
    "enabled": true,
    "text": "Tô Assistindo Isso",
    "secondary_text": "Curtiu? Tem mais.",
    "icon": "thumbs_up",
    "duration": 1.0,
    "position": "bottom_center"
  }
}
```

Duration accepts 0.8–1.2 seconds, clipped to Short duration; no timeline extension
or audio interruption. Position supports bottom_center only. `icon` accepts
thumbs_up (original local ASS vector) or none. Text limit 32 characters;
secondary_text limit 40, empty disables the second line. Fade in/out 120/160 ms.
Small lower strip below default captions; bottom source label is raised to avoid
overlap. Placement reduces face obstruction but cannot guarantee it for arbitrary
scenes or custom caption positions; inspect final shot, disable tag when needed.
