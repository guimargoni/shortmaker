# M3.3 — PASS técnico

04/10/2026. Escopo concluído: legenda premium e assinatura final opcional.
Nenhuma nova dependência, API, publicação ou analytics. Tracking e TTS não
foram modificados; áudio e duração continuam no fluxo existente.

## Verificação

- 61 testes passaram em 36,10 s: os 54 anteriores e 7 novos.
- Novos testes: destaque/palavra inteira/cor, escape seguro de texto ASS,
  legenda antiga, ausência de keywords, assinatura desabilitada, tempo/fade,
  vetor local, herança global/local e validação de configurações.
- Short real Attack on Titan gerado duas vezes com os mesmos cortes, Faber,
  pronunciation overrides, ducking e anime_face_track.
- Antes: `output/m3-3-comparison/before/01-personagens-em-foco-m3-2-focus.mp4`.
- Depois: `output/m3-3-comparison/after/01-personagens-em-foco-m3-2-focus.mp4`.
- Planos: `examples/m3_3_before.json` e `examples/m3_3_after.json`.
- Depois confirmado H.264/AAC, 1080×1920, duração 16,057708 s, igual à
  comparação M3.2. Não há extensão para acomodar a assinatura.
- Frame em 1 s: Eren destacado em #FFD84D, texto restante branco com outline.
- Frame em 15,55 s: assinatura, texto secundário e thumbs_up visíveis;
  source label acima, sem colisão. Rosto não coberto pela assinatura nesta cena.
- Evidências: `output/m3-3-comparison/after/premium.png` e `end-tag.png`.
- Tracking mantém as taxas anteriores: 11/13, 8/8 e 6/11, fallback parcial
  no terceiro corte. Todos os testes anteriores de voz/ducking/captions passam.

Comando de teste:
`.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp output\m3-3-tests`.

## Contrato e limites

Marque até duas palavras em `captions.keywords`; sem marcação não há destaque.
Preset premium é opt-in; JSON antigo mantém aparência anterior. Cor só afeta
legenda, sem modificar texto editorial, pronúncia ou timing. Destaque estático,
sem animação de palavras. Defaults, Short e segmento seguem herança existente.

`branding.end_tag` é opcional e desabilitado por padrão. Duração 0,8–1,2 s,
fade 120/160 ms, rodapé compacto, ícone ASS vetorial original local.
Label inferior sobe apenas quando a assinatura está ativa para evitar colisão.

Rodapé não garante ausência de rosto em qualquer cena/customização; revisar
o último plano continua necessário. Texto limitado para manter layout compacto.
Não há alinhamento palavra a palavra novo ou seleção automática de keywords.
Os renders usam síntese independente; não se afirma identidade binária do áudio.
Revisão auditiva humana destes novos arquivos não foi declarada como concluída.

Implementação encerrada nesta etapa. Nenhum lote de 8–12 Shorts iniciado.
