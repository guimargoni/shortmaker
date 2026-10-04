# Detector de anime M3.2

Modelo: `lbpcascade_animeface.xml`, projeto
[nagadomi/lbpcascade_animeface](https://github.com/nagadomi/lbpcascade_animeface).
Licença: **MIT**, copyright 2011 nagadomi@nurs.or.jp, incluída integralmente no
cabeçalho do XML distribuído em `models/anime/`. Revisão e SHA256 estão em
`manifest.json`. O modelo (~246 KB) é versionado no projeto e dispensa download
durante uso. É um cascade LBP treinado para anime/mangá, não detector humano.

Runtime: `opencv-python-headless` 4.x por CPU, sem interface OpenCV, GPU, API,
cloud, reconhecimento de identidade, landmarks ou YOLO. OpenCV usa licença
[Apache 2.0](https://github.com/opencv/opencv/blob/4.x/LICENSE); a licença do
cascade é distinta.

Amostragem: 2 frames/s de fonte, largura de análise 960 px. Equalização de
histograma; scaleFactor 1.1, minNeighbors 5, tamanho mínimo 24×24. Positivos
isolados são descartados por consistência temporal com amostra adjacente.
Maior rosto tem prioridade; um rosto próximo do foco anterior mantém prioridade
se tiver pelo menos 65% da área do maior, reduzindo trocas. Dois rostos com áreas
comparáveis são agrupados quando a união cabe nos 80% centrais do crop.

Suavização simples mais interpolação smoothstep por frame. Falhas de detecção
breves mantêm o foco por até 0,75 s de fonte; ausência maior volta ao centro.
Sem pelo menos duas amostras confiáveis, todo o segmento usa center crop. Modelo
ausente/inválido, OpenCV indisponível ou erro de análise também fazem fallback.
Cancelamento continua interrompendo o trabalho.

O cascade tem recall limitado em perfil, oclusões e close extremo; detalhes de
cenário podem gerar falsos positivos. Não sabe quem é importante para o roteiro.
Rostos muito afastados não cabem juntos no 9:16. Use keyframes editoriais quando
o automático não corresponder à intenção. As taxas reportadas são sobre amostras,
não uma medição de todos os frames ou precisão anotada por humano.
