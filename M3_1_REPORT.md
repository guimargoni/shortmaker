# M3.1 — Neural Voice Upgrade — PASS

Data: 03/10/2026. **Faber** ficou como padrão após a comparação auditiva feita pelo
usuário, que escolheu Faber entre as duas amostras da mesma frase.

Piper 1.8.0 local/CPU integrado ao módulo TTS. Sem conta, API externa, servidor
remoto ou cobrança por uso. Os modelos foram baixados explicitamente uma vez;
síntese/render não baixam nada. SAPI permanece engine explícita e fallback local.
O renderer `render_pipeline.py`, ducking, captions, timeline e ASS não foram
alterados; continuam recebendo WAV e duração medida do TTS.

## Amostras

Texto exatamente igual nas duas:

> Por mais de cem anos, eles acreditaram estar seguros. Até que isso apareceu.

Parâmetros iguais: rate 1.0 / volume 1.0. Formato PCM16 mono 22.050 Hz.

| Voz | Arquivo | Duração medida | Engine efetiva |
|---|---|---|---|
| Faber medium | `output/m3-1-samples/pt_BR-faber-medium.wav` | 4,446621 s | Piper, sem fallback |
| Cadu medium | `output/m3-1-samples/pt_BR-cadu-medium.wav` | 6,315828 s | Piper, sem fallback |

Requests UTF-8 `.tts.json` e diagnósticos `.tts.result.json` acompanham os WAVs.
O comando abaixo reproduz a comparação em uma nova pasta (sem sobrescrever):

```powershell
.\.venv\Scripts\python.exe -m shortmaker.tts samples --output output\novas-amostras
```

## JSON e fallback

```json
"voice": {
  "engine": "piper",
  "voice_id": "pt_BR-faber-medium",
  "rate": 1.0,
  "volume": 1.0
}
```

Seleção em defaults/Short/voiceover por herança original. `voice` preserva seu
significado SAPI; `voice_id` seleciona o par local ONNX/configuração. O padrão do
plano passa a Piper/Faber; os exemplos com SAPI explícito conservam SAPI.

Ausência do pacote/modelo/configuração ou falha de síntese Piper gera fallback
SAPI, com motivo e engine efetiva no log. Cancelamento não aciona fallback.
O gerador de amostras exige Piper real e falha se ele faltar, impedindo que uma
amostra SAPI seja identificada como Faber/Cadu.

## Render real

Usado o mesmo episódio `AoTDublado01x01.mkv`, fornecido pelo usuário no M3,
mantendo textos, cortes, ducking, captions, hook e configuração de exportação.
Os planos `examples/m3_1_faber.json` e `examples/m3_1_cadu.json` diferem do plano
M3 somente pelo `defaults.voice` explícito.

```powershell
.\.venv\Scripts\python.exe -m shortmaker --source 'C:\Users\guilh\Downloads\[IceBlue]【進撃の巨人】 Shingeki No Kyojin - Attack On Titan 【Temporada 1】 [Dublado PT-BR][1080p]\AoTDublado01x01.mkv' --plan examples\m3_1_faber.json --output output\m3-1-faber
.\.venv\Scripts\python.exe -m shortmaker --source 'C:\Users\guilh\Downloads\[IceBlue]【進撃の巨人】 Shingeki No Kyojin - Attack On Titan 【Temporada 1】 [Dublado PT-BR][1080p]\AoTDublado01x01.mkv' --plan examples\m3_1_cadu.json --output output\m3-1-cadu
```

Ambos os comandos concluíram **2 Shorts / 0 falhas**. Logs confirmam
`solicitado=piper efetivo=piper fallback=None` em todas as narrações.

Narrações Faber: 4,377 / 5,306 / 3,947 / 4,400 s.
Narrações Cadu: 6,362 / 6,920 / 5,097 / 5,677 s.
A voz mais lenta pode produzir o freeze permitido; as regras de overflow são as
mesmas do M3 e nenhum corte/texto foi ampliado para contorná-las.

Saída principal Faber:
`output/m3-1-faber/01-o-comeco-da-mudanca-m3-commentary.mp4`.
Segundo Short no mesmo diretório; versões Cadu em `output/m3-1-cadu/`.

ffprobe do primeiro Faber: **1080×1920, H.264/yuv420p, AAC, 48 kHz estéreo,
21,062708 s**. Os dois MP4s Faber passaram por decode integral sem erros.
Frames em 1 s e 14 s foram inspecionados: hook, legendas e acentos preservados,
legíveis, sem barras acrescentadas. Caption timing usa a duração real Piper,
sem truncamento de narração e sem nova dependência de Whisper.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp output\m3-1-tests-03
```

**44 passed in 27.18s**: 29 testes anteriores preservados + 15 novos.

Os novos testes cobrem Faber/Cadu reais, herança/default/override de engine e voz,
ausência de pacote/modelo/configuração, falha de síntese, fallback SAPI real,
cancelamento sem fallback, rejeição de engine desconhecida/voice_id com traversal,
duração e amplitude do WAV, controles de rate/volume e a mesma montagem M3 com
Piper real. O teste de montagem verifica atenuação entre −20 e −12 dB, restauração
do áudio após narração, ordem/cortes, formato e preservação de saídas após falha.

`tools/setup_piper_models.py` confirmou os hashes dos quatro arquivos dos modelos.
`compileall` e `git diff --check` concluíram sem erros.

## Model cards/licenças e limitações

Veja [docs/voices/README.md](docs/voices/README.md). Cards originais Faber/Cadu,
manifesto com revisão/SHA256 e cópia da GPLv3 do Piper foram registrados.
Ambos os cards informam **CC0 para o dataset**, sem declarar uma licença separada
dos pesos; a origem de treinamento Lessac e sua referência de licença também
ficaram documentadas. Não se confunde licença da engine com a dos modelos.

Síntese por CPU recarrega o modelo em cada worker para preservar cancelamento e
isolamento; existe custo de inicialização. Timings de caption continuam aproximados
por caracteres. Variações pequenas de prosódia/duração entre sínteses são possíveis.
Fallback depende de uma voz SAPI instalada. Qualidade subjetiva: Faber selecionada
pelo usuário; a confirmação de reprodução manual do M3 anterior não é apresentada
como uma nova revisão manual destes MP4s.

**M3.1 PASS** pelos critérios de integração, amostras, render real, preservação
do pipeline e testes. Trabalho encerrado aqui. Publicação, tracking e outras
features não foram iniciados.
