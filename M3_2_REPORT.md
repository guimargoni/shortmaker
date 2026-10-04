# M3.2 — PASS

Validação técnica concluída em 04/10/2026. Escopo encerrado: pronunciation
overrides, anime_face_track e manual_keyframes. M3.1 permanece funcional;
Faber segue padrão e SAPI segue fallback. Nenhuma API externa adicionada.

## Testes e evidências

54 testes passaram em 32,18 s: os 44 anteriores mais 10 novos. Comando:
`.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp output\m3-2-tests-final`.
Cobertura nova: palavra inteira, múltiplas ocorrências, caixa, pontuação,
precedência local/global, texto original/captions preservados, seleção de foco,
suavização, limites, validação manual, detector ausente e render real sem rosto.
Manual keyframes renderizado em fixture de vídeo com trajetória interpolada.

Comparação final, mesmos cortes do episódio local de Attack on Titan e mesmos
parâmetros, diferindo apenas no modo de reframe:

- Center: `output/m3-2-comparison/center/01-personagens-em-foco-m3-2-focus.mp4`
- Anime: `output/m3-2-comparison/anime/01-personagens-em-foco-m3-2-focus.mp4`
- Planos: `examples/m3_2_center_crop.json`, `examples/m3_2_anime_face_track.json`

Inspeção visual de frames: no primeiro corte o center crop corta ambos os rostos
nas bordas; tracking mantém Mikasa inteira em foco. No segundo corte o tracking
inclui Eren e Mikasa juntos. Frames comparáveis estão nos diretórios de saída.
MP4 final confirmado H.264/AAC, 1080×1920, 16,057708 s. Faber, duração medida de
voiceover, ducking e captions usam o fluxo existente. Os testes anteriores de
voz/render passaram; a revisão auditiva humana específica destes novos MP4s
permanece disponível ao usuário, sem alegar que ele já os aprovou.

## Detecção e fallback

2 amostras/s: 25/32 amostras com rosto confiável, aproximadamente 78,1%.
Por corte: 11/13, 8/8 e 6/11. Terceiro corte usou fallback parcial para centro
em 3 amostras; uma ausência breve mantém o foco anterior. Metadata registra
trajetórias, taxas e fallback. A taxa é cobertura de amostras, não precisão.

Os cortes originais do M3 (342–348, 348–355, 361–369 s) não deram detecção
confiável: 0/42, fallback integral sem falhar. Por isso a comparação usa cortes
com rostos frontais (331,5–338, 321–325, 289–294,5 s), sem adicionar descoberta
automática de cenas ao produto.

## Licença e limites

Cascade lbpcascade_animeface MIT, revisão/hash e licença registrados em
`docs/anime/manifest.json`, `docs/anime/README.md` e cabeçalho do XML incluído.
OpenCV headless 4.14.0.94 por CPU. Sem GPU, identidade, landmarks ou YOLO.

Perfis, oclusões e close extremo podem não ser detectados; cenário pode causar
falsos positivos. Filtragem temporal reduz positivos isolados. Rostos afastados
podem não caber juntos; prioridade geométrica não conhece importância narrativa.
Safe area é uma heurística, não garantia para todo rosto/tamanho. Use pontos
manuais nas cenas em que a intenção editorial exigir outro foco.

Único ajuste auxiliar de áudio: fonte sem áudio e sem narração evita loudnorm
sobre silêncio absoluto, que produzia NaN no teste de fallback. O caminho de
narração/ducking permanece preservado. Render usa arquivo de filtro FFmpeg,
validado na versão 9.0.2 instalada.

Nenhuma publicação, analytics, nova transcrição ou feature adicional executada.
