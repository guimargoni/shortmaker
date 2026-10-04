# Piper — modelos e licenças usados no M3.1

Revisão das vozes: `c10ece1aade47bb51c153c893d14e5bf8e5b7117`, repositório
[rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices).
`manifest.json` registra URLs fixadas e SHA256 de ONNX, configuração e model card.
Os cards originais estão versionados aqui; pesos/configs ficam localmente em
`models/piper` e não são incluídos no Git.

| Voz | Idioma/qualidade | Áudio | Licença informada no model card | Card preservado |
|---|---|---|---|---|
| pt_BR-faber-medium | pt-BR / medium / 1 locutor | mono 22.050 Hz | Dataset: CC0 | [Faber](pt_BR-faber-medium.MODEL_CARD.md) |
| pt_BR-cadu-medium | pt-BR / medium / 1 locutor | mono 22.050 Hz | Dataset: CC0 | [Cadu](pt_BR-cadu-medium.MODEL_CARD.md) |

Fontes fixadas: [card Faber](https://huggingface.co/rhasspy/piper-voices/blob/c10ece1aade47bb51c153c893d14e5bf8e5b7117/pt/pt_BR/faber/medium/MODEL_CARD)
e [card Cadu](https://huggingface.co/rhasspy/piper-voices/blob/c10ece1aade47bb51c153c893d14e5bf8e5b7117/pt/pt_BR/cadu/medium/MODEL_CARD).
Ambos apontam para [OHF-Voice/voice-datasets](https://github.com/OHF-Voice/voice-datasets)
e informam fine-tuning a partir de Lessac medium en-US.

Os cards apresentam CC0 na seção Dataset; não declaram uma licença separada para
os pesos ONNX. Essa distinção foi preservada, sem afirmar uma licença adicional
que não consta nos cards. A origem Lessac possui seu próprio
[model card](https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/lessac/medium/MODEL_CARD),
que referencia a [licença do dataset Lessac Blizzard 2013](https://www.cstr.ed.ac.uk/projects/blizzard/2013/lessac_blizzard2013/license.html).

Engine instalada: **piper-tts 1.8.0**, projeto
[OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl), licença **GPLv3**.
A cópia da licença fornecida no pacote está em [PIPER_GPL-3.0.txt](PIPER_GPL-3.0.txt);
a fonte oficial é [COPYING](https://github.com/OHF-Voice/piper1-gpl/blob/main/COPYING).
A licença do código Piper é distinta das informações dos datasets/modelos.
Este registro documenta a instalação local testada; não altera a licença do
SHORTMAKER nem faz uma avaliação jurídica de distribuição ou dos vídeos finais.
