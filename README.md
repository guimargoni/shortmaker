# SHORTMAKER 0.2

Aplicação local para Windows: vídeo fonte + plano JSON → MP4s verticais finalizados,
com montagem, narração offline, ducking, legendas, hook e identificação da fonte.
Não exige CapCut, servidor, banco, login ou API paga. O JSON decide a edição.

## Instalação no Windows

Instale Python 3.11 ou superior com Tcl/Tk (instalador oficial do Python; marque
"Add Python to PATH"). Abra PowerShell na pasta do projeto:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

Instale FFmpeg com libx264, AAC e libass. Baixe a distribuição Windows em
[FFmpeg](https://ffmpeg.org/download.html) / [Gyan](https://www.gyan.dev/ffmpeg/builds/).
Extraia `ffmpeg.exe` e `ffprobe.exe` para `shortmaker\bin\`, ou adicione a pasta
dos dois executáveis ao PATH. Nenhum download ocorre durante a renderização normal.

```powershell
.\bin\ffmpeg.exe -version
.\bin\ffprobe.exe -version
.\.venv\Scripts\python.exe -m shortmaker
```

O ambiente `.venv` e os binários em `bin` já foram preparados nesta máquina.
Não é necessário ativar o ambiente virtual.

## Uso

1. Selecione um `.mp4`, `.mkv`, `.mov` ou `.webm` local.
2. Cole o JSON ou use **Carregar JSON**. Clique **Validar**.
3. Escolha a saída e clique **GERAR SHORTS**.
4. Acompanhe etapas e logs. **CANCELAR** interrompe o trabalho ativo e os próximos
   Shorts; arquivos concluídos permanecem disponíveis.
5. Use **Reproduzir** na revisão local ou **Abrir pasta de saída**. **Aprovar** e
   **Rejeitar** registram sua decisão no metadata JSON local, sem publicar nada.

A geração fica desabilitada até existir uma fonte e um plano válido. Alterar o JSON
exige revalidar. O trabalho roda fora da thread da interface. Falhas de um Short são
registradas e os próximos continuam; nunca há sobrescrita silenciosa.

Os exemplos `examples/minimal_transformative.example.json` e
`examples/full_future.example.json` implementam o contrato 1.1.
`examples/m3_real_source.json` é o plano de smoke test com dois Shorts usado no
episódio informado, com cortes em 05:42–05:48, 05:48–05:55 e 06:01–06:09.
Confira se os cortes e comentários fazem sentido para sua edição.

Também é possível executar o mesmo renderer pelo terminal:

```powershell
.\.venv\Scripts\python.exe -m shortmaker --source 'C:\videos\episodio.mkv' --plan examples\m3_real_source.json --output output
```

O terminal retorna código 1 quando há falhas. A saída informa arquivos concluídos
e erros. Diagnósticos detalhados ficam em `logs/shortmaker.log`.

## M3.1 — voz neural local Piper

Piper é a engine principal; **Faber medium pt-BR** é a voz padrão, escolhida pelo
usuário na comparação com Cadu. Instale o pacote e os dois modelos uma vez:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe tools\setup_piper_models.py
```

O segundo comando baixa somente modelos públicos versionados, valida SHA256 e
coloca-os em `models\piper`. Nesta máquina Piper 1.8.0 e os dois modelos já estão
instalados. Após essa preparação, síntese e render são locais, por CPU, sem API,
conta, servidor ou cobrança por uso. Não ocorre download durante a renderização.

Selecione pelo JSON em `defaults.voice` ou no Short:

```json
"voice": {
  "engine": "piper",
  "voice_id": "pt_BR-faber-medium",
  "rate": 1.0,
  "volume": 1.0
}
```

Para Cadu, use `pt_BR-cadu-medium`. Os mesmos campos podem ser sobrescritos em
`timeline[].voiceover`. `rate > 1` acelera; `volume` aceita 0–1. O WAV medido mantém
as regras originais de duração, overflow, ducking e captions. `SHORTMAKER_PIPER_MODELS`
pode apontar para outra pasta de modelos locais. O par `.onnx` + `.onnx.json` precisa
ter o nome do `voice_id`.

Se Piper, o modelo ou a configuração faltarem, ou a síntese Piper falhar, usa SAPI
local e registra o motivo no log. `engine: sapi` explícito continua selecionando
SAPI. `voice` continua sendo nome/ID SAPI; `voice_id` seleciona exclusivamente Piper.
Cancelamento interrompe o processo e não dispara fallback. Falha também no SAPI
gera erro legível. Os exemplos históricos com SAPI explícito são preservados.

Amostras comparáveis, sempre com a frase fixa
“Por mais de cem anos, eles acreditaram estar seguros. Até que isso apareceu.”:

```powershell
.\.venv\Scripts\python.exe -m shortmaker.tts samples --output output\novas-amostras
```

Gera `pt_BR-faber-medium.wav` e `pt_BR-cadu-medium.wav` com a mesma frase/rate/volume,
mais parâmetros e diagnóstico `.tts.result.json`. Amostras não aceitam fallback e
não sobrescrevem arquivos existentes; escolha outra pasta para repetir.
Use `--rate 1.1` ou `--volume 0.8` para comparar com parâmetros iguais nas duas.

Os exemplos `examples/m3_1_faber.json` e `examples/m3_1_cadu.json` mantêm os cortes
e textos do M3 e mudam somente `defaults.voice`. Consulte
[model cards e licenças](docs/voices/README.md) e [evidências M3.1](M3_1_REPORT.md).

## Fallback offline SAPI

`pyttsx3` usa vozes SAPI Desktop instaladas no Windows, sem conta ou internet.
A preferência automática é uma voz portuguesa; na ausência dela usa a voz padrão
instalada. `voiceover.voice` pode conter o nome ou ID de uma voz. Para listar:

```powershell
.\.venv\Scripts\python.exe -m shortmaker.tts voices
```

Nesta máquina foi validada **Microsoft Maria Desktop — Portuguese (Brazil)**.
Se não houver voz funcional, instale uma voz em **Configurações > Hora e idioma >
Fala** e confirme que aparece na listagem SAPI Desktop; vozes exclusivas OneCore
podem não aparecer. Existe fallback local para SAPI direto se `save_to_file` falhar.
Não há fallback para serviço pago ou online. Erros de SAPI pedem correção da voz.

SAPI e Tcl/Tk precisam das permissões normais da sessão de Windows. Um sandbox que
nega acesso a COM/Tcl pode falhar apesar de a aplicação funcionar fora dele.

A narração nunca é truncada silenciosamente: excedente de até 1,5 s (incluindo
`start_offset`) congela o último frame; acima disso o segmento falha com instrução
para ampliar `end`, reduzir `text` ou aumentar `voiceover.rate`.

## Contrato e comportamento

Fontes de verdade: `MASTER_SPEC.md`, `JSON_CONTRACT.md`, `ACCEPTANCE_TESTS.md` e
`schemas/shortmaker.schema.json`. A herança faz deep merge de padrões internos,
defaults do plano, overrides do Short e do segmento; listas substituem listas.
Campos futuros são preservados no metadata JSON e não iniciam ações de rede.

- Exportação 1080×1920, H.264/AAC, yuv420p, áudio estéreo 48 kHz e faststart.
- `center_crop` preenche a tela. `manual_x`/`manual_y` são posições normalizadas
  0–1 sobre a área excedente; `zoom >= 1` amplia antes do crop.
- `face_track`, `smart_track` e `fit_blur` avisam e usam center crop; com `strict`
  ativado, falham. Para anime, use `anime_face_track` descrito abaixo.
- `speed` afeta imagem e áudio. Sem narração, o modo `duck` aplica redução ao
  segmento todo; com narração reduz somente seu intervalo. `keep` e `mute` têm
  prioridade sobre ducking.
- Legendas ASS da narração usam o texto conhecido, duração real da voz e proporção
  de caracteres, até duas linhas. Nenhum Whisper é executado para a narração.
- Hook e source label usam ASS. `overlay_text` pode ser string ou objeto com
  `text`, `start`, `end`, `position` e `style`; tempos são locais ao segmento.
- `cut` é padrão; `fade` faz fade simples para/de preto, sem sobrepor clips.
- Normalização final tem alvo padrão −16 LUFS / −1,5 dBTP; é o filtro loudnorm de
  uma passagem, não medição de mastering em duas passagens.
- Nomes seguem `{index:02d}-{slug}-{id}.mp4`, sanitizados para Windows; colisões
  ganham `-2`, `-3` etc. O título YouTube precede editorial e ID no slug.
- Metadata sidecar preserva plano resolvido e publicação futura. Nada é enviado
  para YouTube/TikTok/Instagram e nenhum agendamento é executado.
- Avisos editoriais não impedem renderização e não são decisão oficial de
  monetização. O aplicativo não garante monetização ou ausência de claims.

## Transcrição opcional de diálogo

Somente segmentos sem narração, com `captions.enabled=true` e
`captions.source_dialogue=true` (ou modo `source`, `source_dialogue`, `both`) acionam
faster-whisper. Instale apenas se for usar:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[transcription]"
```

CPU/int8 é suportado. O primeiro uso de um nome como `small` pode baixar o modelo;
para uso totalmente offline, coloque um caminho de modelo já disponível em
`whisper_model`. Whisper opcional não bloqueia o caminho principal do produto.

## Verificação

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

A suíte inclui testes do contrato, timecodes, herança, nomes, overflow, avisos,
GUI Windows, cancelamento de subprocesso, renders reais com SAPI/Piper/FFmpeg,
seleção/fallback de engine e controles de voz. A suíte M3.1 passou com 44 testes.
Execute em sessão normal Windows com as dependências instaladas. Se alternar
entre sandbox e sessão normal, use uma pasta temporária nova e desabilite cache:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp output\test-run-new
```

Veja `M3_REPORT.md` para resultados e evidências do episódio real. Os MP4s do smoke
test ficam em `output\m3-real\`. Reveja imagem e som no player padrão ou navegador.

## Limites desta versão

Outras engines, tracking genérico, transições complexas e publicação são futuros.
Timings de legenda são aproximados por caracteres, sem alinhamento palavra
a palavra. Processamento é sequencial por CPU; vídeos longos podem demorar.
O arquivo fonte permanece intacto. Installer e polimento visual não fazem parte
do MVP.

## M3.2 — pronúncia e enquadramento de anime

`defaults.voice.pronunciation_overrides` aceita um dicionário como
`{"Eren":"Éren","Mikasa":"Micássa"}`. O mesmo campo em `shorts[].voice`
sobrescreve entradas globais. Só o texto enviado ao TTS muda: legendas e texto
editorial permanecem originais. Substituições respeitam palavra inteira,
priorizam caixa exata e registram as aplicações no log e no resultado TTS.

Use `"reframe":{"mode":"anime_face_track"}` em defaults de vídeo ou segmento.
O cascade anime MIT incluído roda em OpenCV/CPU e cai automaticamente para
center crop quando não há detecção confiável. Veja `docs/anime/README.md` para
licença, parâmetros e limitações. Não há download durante o render.

Controle editorial: `{"mode":"manual_keyframes","keyframes":[{"at":0,
"x":0.35,"y":0.42},{"at":4.5,"x":0.68,"y":0.40}]}`.
X/Y são o centro normalizado do crop; tempos são locais ao segmento após speed,
antes do freeze final. Interpolação suave e limites do frame são aplicados.
Keyframes devem estar ordenados e dentro da duração visual.

Os planos `examples/m3_2_center_crop.json` e `examples/m3_2_anime_face_track.json`
geram a comparação com os mesmos cortes, Faber, legendas e áudio. Use diretórios
de saída distintos. Validação: 54 testes, FFmpeg 9.0.2; detalhes em `M3_2_REPORT.md`.

## M3.3 — legenda premium e assinatura

Ative `captions.style_preset: "premium"`, `highlight_keywords: true`,
`highlight_color: "#FFD84D"` e marque até duas palavras em `keywords`.
Sem palavras marcadas, não há destaque. JSONs antigos mantêm o estilo anterior.

`branding.end_tag.enabled: true` ativa a assinatura nos últimos 0,8–1,2 s;
`text`, `secondary_text`, `icon: "thumbs_up"` e `duration: 1.0` são configuráveis.
O ícone é um desenho ASS local. Não adiciona duração nem interrompe áudio.
Use `examples/m3_3_before.json` e `examples/m3_3_after.json` para comparar.
Confira a cena final: o rodapé discreto não garante ausência de rostos em toda
composição. Detalhes e parâmetros em `JSON_CONTRACT.md`.

## M3.4 — edição cinematográfica por JSON

`timeline[].effects` aceita punch_in, slow_zoom, freeze_frame, text_card,
speed_change, fade e hard_cut_marker. Tudo é opt-in; nenhum efeito é criado
automaticamente. `editing.pace` define defaults; warnings editoriais são opcionais.
Crossfade curto usa `transition_out: {"type":"crossfade","duration":0.12}`.

Use `examples/m3_4_before.json` e `examples/m3_4_after.json` para comparar.
O exemplo usa 1 punch-in, 1 slow zoom, 1 card e 1 freeze curto. Sem crossfade.
Tempos, limites e regras de áudio estão em `JSON_CONTRACT.md`.

Remoção de pausas é conservadora: por padrão preserva reações e não corta.
Só bordas pretas com PCM exatamente zero e autorização editorial explícita para
dispensar a pausa podem ser removidas; fala/cenas/reação não são inferidas por IA.
Intermediários lossless de efeitos temporais exigem espaço temporário adicional.
