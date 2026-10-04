# Evidências do M3 — 03/10/2026

**M0 PASS · M1 PASS · M2 PASS · M3 PASS.** Implementação, verificações
automatizadas e confirmação manual de reprodução no Windows concluídas.
Nenhuma stop condition técnica foi encontrada.

Em 03/10/2026, o usuário confirmou reprodução normal no Windows, narração audível,
ducking funcionando, legendas presentes e boa qualidade de vídeo, autorizando
registrar M3 PASS. Trabalho encerrado neste marco; publicação e outros itens não
foram iniciados, conforme instrução explícita do usuário.

## Execuções

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp output\m3-tests-02
```

Resultado: **29 passed in 8.24s**, incluindo SAPI e render reais. Python 3.12.14,
Pydantic 2.13.5, pyttsx3 2.99, FFmpeg/ffprobe 9.0.2, Tcl/Tk 8.6.12.

```powershell
.\.venv\Scripts\python.exe -m shortmaker --source 'C:\Users\guilh\Downloads\[IceBlue]【進撃の巨人】 Shingeki No Kyojin - Attack On Titan 【Temporada 1】 [Dublado PT-BR][1080p]\AoTDublado01x01.mkv' --plan examples\m3_real_source.json --output output\m3-real
.\.venv\Scripts\python.exe tests\smoke_real_gui.py 'C:\Users\guilh\Downloads\[IceBlue]【進撃の巨人】 Shingeki No Kyojin - Attack On Titan 【Temporada 1】 [Dublado PT-BR][1080p]\AoTDublado01x01.mkv'
```

Ambos produziram dois Shorts sequenciais, com zero falhas. O smoke test usa a GUI
real (`Tk`/`MainWindow`, carregar texto, validar, iniciar worker, polling de eventos)
com janela recolhida para o teste. Registrou **180 heartbeats**, maior intervalo
**0,125 s** durante renderização. Aprovação/rejeição local também verificadas.
Arquivos da segunda execução em `output/m3-gui/`.

Saídas principais:

- `output/m3-real/01-o-comeco-da-mudanca-m3-commentary.mp4`
- `output/m3-real/02-o-contraste-da-cena-m3-second.mp4`
- Metadata JSON ao lado de cada arquivo.

## Gates

| Gate | Evidência | Resultado |
|---|---|---|
| A | Tk inicia; teste de dependência ausente em português; sem serviços externos | PASS |
| B | Ambos os exemplos, campo end exato, deep merge e overrides; futuros preservados | PASS |
| C | Render real + teste fonte azul/vermelho/verde na ordem JSON, duração ±0,25 s | PASS |
| D | Maria SAPI em segmentos 1 e 3; áudio original no 2; isolamento de tom verifica redução −16 dB e restauração; overflow testado | PASS |
| E | ffprobe 1080×1920/H.264 High/yuv420p/AAC LC/48 kHz/estéreo; decode integral sem erros; frames/UTF-8 conferidos; usuário confirmou reprodução normal no Windows e boa qualidade | PASS |
| F | Dois Shorts reais; teste com falha entre saídas válidas preserva e continua; colisões/nome seguro | PASS |
| G | GUI real durante render, heartbeat, etapas; cancelamento mata processo e recusa trabalho futuro; open folder verificado por chamada | PASS |
| H | Aviso sem narração mantém render permitido e declara que não é decisão oficial | PASS |
| I | 29 testes verdes; README de instalação/FFmpeg/SAPI/fallback; exemplos | PASS |

Inspeção visual: `hook-caption.png` em 1 s, `caption.png` em 15,5 s e
`source-label-last.png` em 22 s. Hook/legendas com acentos legíveis, duas linhas,
crop sem barras acrescentadas; source label legível e separado das legendas.

Primeiro MP4: duração **22,944792 s**. Medição do áudio final por loudnorm:
**−16,04 LUFS** e **−1,50 dBTP** (`input_i`/`input_tp` da análise do arquivo já
normalizado). A renderização inclui freeze permitido quando a narração excede o
corte, sem truncá-la.

## Limites da verificação

O navegador integrado bloqueou o protocolo `file:` na tentativa de prévia.
Não foi usada alternativa para contornar essa política. A reprodução manual no
Windows e a narração audível foram confirmadas pelo usuário; o decode automatizado
é uma evidência separada. Whisper opcional não foi instalado/executado.
Tracking, engines futuras e publicação permanecem fora do MVP.

## Smoke test manual

1. Execute `.\.venv\Scripts\python.exe -m shortmaker` na pasta do projeto.
2. Selecione o episódio, carregue `examples/m3_real_source.json` e valide.
3. Clique GERAR SHORTS. Confira etapas, responsividade e dois arquivos concluídos.
4. Reproduza o Short: hook inicial, três cortes, Maria nos segmentos 1 e 3,
   ducking, legendas e rótulo final. Aprove/rejeite localmente.
5. Se desejar verificar cancelamento, gere novamente e cancele durante a primeira
   renderização. Arquivos de execuções anteriores devem permanecer intactos.

## Arquivos implementados

`pyproject.toml`, `requirements.txt`, `.gitignore`, `README.md`, `M3_REPORT.md`,
`examples/m3_real_source.json`, `src/shortmaker/` (contrato, validação, timecodes,
paths, probe, processos, SAPI, ASS, áudio, timeline, renderer, GUI e revisão),
`tests/test_contract.py`, `tests/test_runtime.py`, `tests/smoke_real_gui.py`,
`output/.gitkeep`, `logs/.gitkeep`.
Os critérios das quatro instruções originais, schema e exemplos recebidos foram
preservados. A checklist de aceitação foi marcada como concluída após a confirmação
manual do usuário; os critérios não foram alterados.
Binários, venv, saídas e logs são locais e estão ignorados pelo Git.
