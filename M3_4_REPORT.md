# M3.4 — PASS técnico

04/10/2026. Edição opt-in dirigida pelo JSON concluída, sem reescrever o motor.
Render base preservado; módulos separados compõem os eventos solicitados.
Nenhuma dependência/API nova, IA editorial, publicação ou milestone M4+ iniciada.

## Testes

**90 testes passaram em 36,60 s**: 61 anteriores + 29 novos.
Comando definitivo:
`.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp output\m3-4-tests-complete`.

Cobertura: JSON antigo, sete tipos de eventos válidos, parâmetros inválidos,
speed bounds/duração/overlap, presets de pace, trim_policy, warnings opcionais,
crossfade real/duração, vídeo 1080×1920, freeze após crop móvel e modos de áudio
continue/duck/mute. Teste FFT confirma 440 Hz após retiming 0,8x (pitch preservado).
Teste de trimming remove bordas pretas com PCM zero dentro de 300 ms por borda;
áudio nãozero e erro de análise não cortam. Preservação de reação evita análise/corte.
Regressões anteriores de Faber/SAPI, tracking, captions, branding e ducking passam.

## Comparação real definitiva

Fonte: episódio local AoTDublado01x01.mkv já autorizado. Mesmos cortes e textos.

- Before M3.3: `output/m3-4-comparison/before/01-personagens-em-foco-m3-2-focus.mp4`
- After definitivo: `output/m3-4-comparison/cinematic/01-personagens-em-foco-m3-2-focus.mp4`
- Planos: `examples/m3_4_before.json`, `examples/m3_4_after.json`.
- Outros diretórios after/final-after são iterações de teste, não a referência final.

Efeitos usados, estritamente abaixo do teto solicitado:

1. Slow zoom no primeiro corte, 0–2 s, escala 1→1,04.
2. Punch-in no primeiro corte, 3,4 s, duração 0,5 s, escala alvo 1,06.
3. Card subtle no segundo corte, 0,5 s, duração 1,1 s:
   “A segurança parecia garantida.”
4. Freeze no terceiro corte, 2,4 s, duração 0,45 s; áudio continua.

Sem speed change ou crossfade no smoke editorial: foram validados em fixture
controlada e não eram necessários nesta montagem. Os cortes secos foram mantidos.
Trim solicitado com preserve_dialogue/preserve_reaction=true: **zero remoção**
nos três clips, registrado em metadata. Nenhuma fala ou reação foi cortada.

MP4 final: H.264/AAC, **1080×1920**, **16,057708 s**, decodificação completa sem
erros. Captions premium, highlight, assinatura, fonte Faber e ducking mantidos.
Tracking: 11/13, 8/8, 6/11 amostras com rosto; mesmo fallback parcial conhecido.
Durante o freeze, a área visual do rosto entre 13,02 e 13,19 s tem diferença média
de apenas 0,044/255 por canal (compressão), confirmando quadro enquadrado parado.
Captions continuam atualizando sobre o quadro congelado.

Inspeção visual dos frames focus/card/end-tag: zoom pequeno mantém rosto inteiro;
card ocupa céu acima dos personagens; legendas e branding legíveis. A alteração
é contida, com detalhe editorial adicional sem esconder a cena ou virar slideshow.
Frames estão em `output/m3-4-comparison/cinematic/`. A avaliação humana da
naturalidade/ritmo e a audição dos novos MP4s ainda não foram declaradas concluídas.

## Arquivos alterados/criados nesta milestone

- `src/shortmaker/editing_models.py`: contrato dos eventos/policy/pace.
- `src/shortmaker/editing.py`: composição de tempo, zoom, cards, freeze,
  micro trim conservador, crossfade e warnings.
- `src/shortmaker/render_pipeline.py`: chamadas pontuais, freeze após reframe,
  integração de crossfade e metadata editing_report.
- `src/shortmaker/models.py`, `settings.py`, `constants.py`: campos/herança/defaults.
- `src/shortmaker/timeline.py`, `validation.py`: duração e validação de eventos.
- `schemas/shortmaker.schema.json`: schema dos novos campos.
- `tests/test_m3_4.py`: 29 novos testes.
- `examples/m3_4_before.json`, `examples/m3_4_after.json`: comparação.
- `JSON_CONTRACT.md`, `README.md`, `ACCEPTANCE_TESTS.md`, `M3_4_REPORT.md`: documentação.

## Limitações e próxima ação

Não há detecção semântica de pausas dispensáveis. Remoção automática só funciona
em bordas totalmente pretas com áudio exatamente zero e autorização explícita
para dispensar a pausa; por padrão não remove reações. Clips com voz/eventos/
keyframes não são recortados automaticamente. Não corta silêncios internos.

Freeze substitui vídeo no intervalo, não adiciona tempo. Speed change mantém
narração em seu relógio independente, como documentado; o editor deve verificar
sentido/sincronia narrativa. Zoom centrado após reframe exige escala contida e
revisão em close extremo. Cards em área superior não garantem ausência de rosto
em toda cena. Crossfade curto pode misturar textos/áudio na junção; não foi usado
no smoke e só transition_out entre clips tem composição. Marcador não cria corte.
Perfis definem defaults, não escolhem cenas ou criam efeitos. Intermediários
lossless de retiming/modos de áudio exigem espaço temporário adicional.

Nenhuma regressão séria detectada. Nenhuma stop condition técnica acionada.
Próxima ação exata: assistir aos MP4s before/cinematic com som, comparar ritmo,
continuidade, foco e naturalidade e confirmar a preferência editorial. Encerrado
aqui, sem iniciar outras features.
