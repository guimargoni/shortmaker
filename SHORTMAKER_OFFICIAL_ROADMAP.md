# SHORTMAKER — ROADMAP OFICIAL

## 0. Visão do produto

SHORTMAKER deve evoluir de um renderizador orientado por JSON para uma linha de produção local de Shorts com IA.

Fluxo-alvo final:

1. Usuário seleciona vários vídeos.
2. Para cada vídeo, informa identificação da obra e quantidade desejada de Shorts.
3. O programa transcreve e analisa localmente.
4. Um motor editorial com IA propõe os melhores Shorts.
5. O sistema gera automaticamente os JSONs editoriais.
6. O Render Engine produz os vídeos finais.
7. O usuário revisa cada resultado em uma fila.
8. O usuário aprova, rejeita ou regenera.
9. A IA gera título, descrição, tags e outros metadados.
10. O usuário define/aprova data e horário.
11. O programa faz upload e agenda no YouTube.
12. Mais tarde, analytics reais alimentam decisões editoriais futuras.

Princípio central:

> Automatizar ao máximo sem sacrificar qualidade, originalidade editorial ou controle humano antes da publicação.

---

# 1. Estado atual

## M0 — Foundation
**PASS**

Base Python, UI local, JSON, validação, FFmpeg e testes.

## M1 — Rendering Core
**PASS**

Corte, montagem, 9:16, exportação H.264/AAC.

## M2 — Publishable Short
**PASS**

Hook, captions, ducking, múltiplos trechos e vídeo final.

## M3 — Real Source Gate
**PASS**

Episódio real validado.

## M3.1 — Neural Voice
**PASS**

Piper/Faber como voz principal.
Cadu como alternativa.
SAPI como fallback.

## M3.2 — Pronunciation + Anime Smart Reframe
**PASS**

- pronunciation overrides;
- anime face tracking;
- fallback para center crop;
- manual keyframes.

## M3.3 — Premium Captions + Branding
**EM EXECUÇÃO / PENDENTE DE GATE**

Escopo:
- captions premium;
- destaque de palavras-chave;
- end tag do canal;
- identidade visual inicial.

M4 só deve começar depois de M3.3 estar PASS e sem regressão.

---

# 2. Arquitetura alvo

O sistema deve ser composto por módulos independentes.

```text
SOURCE QUEUE
    ↓
LOCAL ANALYSIS
    ↓
EDITORIAL ENGINE
    ↓
JSON PLAN
    ↓
RENDER ENGINE
    ↓
REVIEW QUEUE
    ↓
METADATA ENGINE
    ↓
PUBLISHER / SCHEDULER
    ↓
ANALYTICS FEEDBACK
```

O Render Engine atual deve permanecer isolado e reutilizável.

Não reconstruir o núcleo já funcional.

---

# 3. Trilha A — Automação

# M4 — Source Queue

## Objetivo

Permitir selecionar vários vídeos antes de gerar.

## UI

Tabela/lista com uma linha por fonte:

| Arquivo | Identificação | Shorts | Perfil | Output | Status |
|---|---|---:|---|---|---|
| ep01.mkv | Attack on Titan S1E1 | 4 | Auto | pasta | Aguardando |

## Cada item deve ter

- caminho do arquivo;
- nome/identificação livre;
- obra;
- temporada opcional;
- episódio opcional;
- quantidade de Shorts;
- perfil editorial;
- pasta de saída;
- status;
- remover da fila.

## Perfis iniciais

- Automático
- Impacto
- Análise
- Curiosidade
- Emoção
- Recomendação

## Funcionalidades

- selecionar vários arquivos de uma vez;
- editar os campos diretamente na lista;
- quantidade de Shorts por item via dropdown/spinbox;
- persistir a fila localmente;
- carregar/salvar sessão;
- iniciar processamento apenas dos itens selecionados;
- cancelar fila.

## Não fazer ainda

- IA;
- publicação;
- metadata;
- YouTube.

## PASS

M4 passa quando o usuário consegue colocar vários episódios na fila, configurar quantidade individual e disparar o processamento sequencial sem quebrar o Render Engine.

---

# M5 — Local Analysis Engine

## Objetivo

Extrair do vídeo informação suficiente para uma IA editorial trabalhar sem receber o vídeo bruto inteiro.

## Pipeline local

```text
video
 ↓
ffprobe
 ↓
audio
 ↓
transcription
 ↓
scene detection
 ↓
silence / speech segmentation
 ↓
sample frames
 ↓
structured analysis package
```

## Dados extraídos

- duração;
- transcrição;
- timestamps;
- falas;
- mudanças de cena;
- trechos com silêncio;
- densidade de fala;
- detecções de rosto;
- frames representativos;
- intensidade visual simples;
- opcionalmente OCR de texto na tela.

## Tecnologia preferida

- faster-whisper local;
- FFmpeg;
- OpenCV;
- PySceneDetect ou lógica equivalente simples.

## Output

Arquivo interno, por exemplo:

```json
{
  "source_id": "...",
  "duration": 1440,
  "segments": [],
  "scenes": [],
  "speech": [],
  "face_activity": [],
  "representative_frames": []
}
```

## PASS

Um episódio completo gera um pacote estruturado utilizável pelo motor editorial sem intervenção humana.

---

# M6 — Editorial Engine com IA

## Objetivo

Eliminar a necessidade de o usuário colar manualmente um JSON feito fora do programa.

## Entrada da IA

- identificação da obra;
- quantidade desejada de Shorts;
- transcrição;
- cenas;
- timestamps;
- contexto editorial;
- regras do canal;
- JSON schema oficial.

## Saída

O mesmo JSON que hoje é criado manualmente.

## Modos

### Manual
Usuário cola JSON, como hoje.

### Auto
Programa gera JSON por IA.

### Assistido
Programa gera e usuário pode revisar o JSON antes do render.

## Requisitos editoriais

Preservar todas as regras já definidas:

- áudio original importante não deve ser atropelado;
- narração transformativa;
- variedade de ângulos;
- 35–55s como faixa preferencial;
- captions;
- anime face tracking;
- pronunciation overrides;
- branding;
- hooks;
- metadados editoriais.

## Provedor de IA

Criar interface abstrata:

```text
EditorialProvider
```

para permitir no futuro:

- OpenAI;
- outro provedor;
- modelo local.

Nenhum provedor deve ficar acoplado ao Render Engine.

## Controle de custo

- enviar texto/estrutura, não vídeo completo;
- cachear análise;
- cachear resultado editorial;
- permitir regenerar apenas um Short;
- não repetir análise local desnecessariamente.

## PASS

Selecionar um episódio + escolher “4 Shorts” + clicar gerar produz automaticamente um JSON editorial válido e 4 vídeos finais.

---

# M7 — Review Queue

## Objetivo

Transformar os outputs em itens revisáveis dentro do próprio programa.

## Cada Short deve mostrar

- thumbnail;
- botão Preview;
- origem;
- duração;
- título editorial;
- status;
- Aprovar;
- Rejeitar;
- Regenerar;
- Abrir arquivo.

## Estados

- Generated
- Needs Review
- Approved
- Rejected
- Regenerating
- Failed

## Regeneração

Permitir:

- regenerar vídeo inteiro;
- regenerar apenas narração;
- regenerar metadata;
- regenerar editorial;
- usar JSON editado.

## Persistência

A fila deve sobreviver ao fechamento do aplicativo.

SQLite passa a ser justificável a partir daqui.

## PASS

Usuário consegue gerar lote, assistir dentro/através do app e aprovar/rejeitar individualmente.

---

# M8 — Metadata Engine

## Objetivo

Gerar automaticamente informações de publicação somente para vídeos aprovados.

## Gerar

- título;
- descrição;
- hashtags;
- tags;
- nome interno;
- comentário fixado opcional;
- sugestão de horário;
- categoria quando aplicável.

## UI

Cada item aprovado mostra:

```text
Metadata: [⟳] [✓]
```

Estados:

- Pending
- Generating
- Ready
- Failed

## Regras

- título não pode ser clickbait falso;
- evitar caps excessivo;
- descrição curta e natural;
- metadata deve refletir o conteúdo real;
- permitir edição humana.

## PASS

Short aprovado recebe metadata completa com um clique ou automaticamente.

---

# M9 — Publishing Queue + Scheduling

## Objetivo

Criar a segunda lista imaginada pelo usuário: vídeos aprovados aguardando publicação.

## Cada linha

- thumbnail;
- título;
- data;
- horário;
- status;
- botão de aprovação;
- metadata status;
- upload status.

## Horários padrão iniciais

- 11:00
- 14:00
- 18:00
- 21:00

Configuráveis.

## Distribuição automática

Exemplo:

12 Shorts
4 por dia

Resultado:

```text
Dia 1 — 11h, 14h, 18h, 21h
Dia 2 — 11h, 14h, 18h, 21h
Dia 3 — 11h, 14h, 18h, 21h
```

## Regras

- nenhum upload sem aprovação;
- usuário pode alterar data/hora;
- conflitos devem ser detectados;
- timezone explícito;
- fila persistente.

## PASS

Usuário consegue selecionar vídeos aprovados e montar a agenda sem acessar o YouTube Studio.

---

# M10 — YouTube Integration

## Objetivo

Upload e agendamento real no YouTube.

## Requisitos

- OAuth oficial;
- credenciais do usuário;
- upload resumable;
- título;
- descrição;
- tags;
- privacy;
- scheduled publish;
- retry;
- progress;
- tratamento de quota;
- estados claros.

## Status por item

```text
Render      ✓
Metadata    ✓
Approved    ✓
Uploading   …
Scheduled   ✓
```

ou:

```text
Upload      ✕
[Retry]
```

## Segurança

- tokens locais protegidos adequadamente;
- nunca embutir segredo no repositório;
- nenhuma publicação sem aprovação explícita.

## PASS

Um Short aprovado é enviado e aparece corretamente agendado no canal.

---

# M11 — Batch Production

## Objetivo

Chegar à experiência:

> selecionar 10 episódios → pedir 4 Shorts de cada → gerar tudo → revisar → aprovar → agendar.

## Requisitos

- worker queue;
- limite de concorrência;
- processamento overnight;
- retry;
- pausa/retomada;
- logs por job;
- estimativa de progresso;
- recuperação após fechamento/crash.

## PASS

40+ Shorts podem ser processados numa fila sem exigir acompanhamento constante.

---

# M12 — Analytics Feedback

## Objetivo

Usar dados reais do canal para melhorar decisões futuras.

## Métricas

- views;
- viewed vs swiped away;
- average view duration;
- retention;
- likes;
- comments;
- shares;
- subscribers gained;
- horário;
- duração;
- tipo editorial;
- obra;
- hook style.

## Uso

O sistema não deve “auto-otimizar” silenciosamente.

Deve gerar recomendações como:

```text
Curiosity teve +18% retenção que Recommendation.
Shorts de 40–47 s tiveram melhor conclusão.
21h teve melhor início de distribuição.
```

## PASS

O Editorial Engine consegue receber performance histórica como contexto opcional.

---

# 4. Trilha B — Qualidade de edição

Essa trilha ocorre paralelamente à automação.

# Q1 — Captions & Branding
Corresponde ao M3.3.

- premium captions;
- keyword highlighting;
- end tag;
- identidade do canal.

---

# Q2 — Dynamic Punch-ins

Adicionar ao JSON:

```json
"effects": [
  {
    "type": "punch_in",
    "at": 3.2,
    "duration": 0.5,
    "scale": 1.08
  }
]
```

Usar em:
- reação;
- revelação;
- impacto;
- expressão.

Nunca aplicar em excesso.

---

# Q3 — Micro Dead-Time Removal

Detectar e cortar:

- pausas mortas;
- silêncios desnecessários;
- frames redundantes;
- intervalos sem informação.

Parâmetro editorial:

```json
"pace": "normal"
```

Valores:

- dramatic
- normal
- fast

---

# Q4 — Advanced Voice

Objetivo: deixar narração progressivamente menos parecida com TTS.

Explorar:

- voz neural local melhor;
- pausas explícitas;
- emphasis;
- ritmo por segmento;
- emoção;
- prosódia;
- modelos maiores opcionais.

O sistema deve continuar aceitando Piper/Faber como fallback.

Nunca depender de uma API paga para funcionar.

---

# Q5 — Contextual Audio

Melhorias:

- ducking variável;
- fade;
- preservar SFX importantes;
- normalização por segmento;
- detecção de diálogo;
- opcionalmente música de fundo licenciada/original.

Não adicionar música automaticamente só para “preencher”.

---

# Q6 — Motion Graphics

Permitir:

- título em 2 etapas;
- boxes;
- arrows;
- subtle emphasis;
- freeze frame;
- spotlight;
- blur seletivo;
- simple callouts.

Tudo dirigido pelo JSON.

---

# Q7 — Advanced Reframe

Evoluir além de face tracking:

- personagem narrativamente importante;
- múltiplos rostos;
- troca de foco suave;
- composição de dois personagens;
- object tracking;
- keyframes automáticos + manuais.

---

# Q8 — Editorial Timeline v2

Permitir eventos mais ricos:

```json
{
  "type": "source_clip",
  "start": "...",
  "end": "...",
  "focus": {},
  "voiceover": {},
  "effects": [],
  "overlays": [],
  "audio": {}
}
```

E também:

- freeze_frame;
- replay;
- speed_change;
- text_card;
- still_image;
- transition;
- callback.

---

# Q9 — Originality Engine

A IA editorial deve evitar que todos os Shorts pareçam iguais.

Variar conscientemente:

- abertura;
- ritmo;
- quantidade de narração;
- sequência de cenas;
- tipo de conclusão;
- CTA;
- estrutura narrativa.

Objetivo:

> identidade consistente sem aparência de conteúdo industrial repetitivo.

---

# 5. Ordem recomendada

Não seguir apenas números.

Ordem ideal por impacto/custo:

```text
M3.3
 ↓
M4
 ↓
Q2 + Q3
 ↓
M5
 ↓
M6
 ↓
M7
 ↓
Q4
 ↓
M8
 ↓
M9
 ↓
M10
 ↓
M11
 ↓
Q5–Q9 gradualmente
 ↓
M12
```

Motivo:

- primeiro melhorar levemente o produto atual;
- depois reduzir trabalho manual;
- depois construir revisão;
- só então publicação;
- analytics somente após haver volume real.

---

# 6. Prioridades

## P0 — não quebrar

Sempre preservar:

- JSON manual;
- render local;
- Faber;
- captions;
- ducking;
- tracking;
- saída 1080x1920;
- modo sem API.

## P1 — maior retorno

1. qualidade editorial;
2. source queue;
3. IA editorial;
4. review queue;
5. metadata;
6. scheduling.

## P2 — refinamentos

- transições;
- efeitos;
- motion;
- vozes adicionais;
- analytics sofisticado.

---

# 7. Regras de desenvolvimento

1. Uma milestone por vez.
2. Cada milestone tem PASS/BLOCKED.
3. Não avançar com regressões.
4. Não ampliar escopo durante implementação.
5. Codex implementa; decisões de produto devem estar fechadas antes.
6. Testar com vídeos reais.
7. Sempre manter fallback.
8. Evitar reescrever o que já funciona.
9. Features caras/externas devem ser opcionais.
10. O usuário sempre mantém controle final de publicação.

---

# 8. Visão da UI final

## Página Produção

```text
SHORTMAKER

[ + Adicionar vídeos ]

Arquivo            Identificação             Shorts   Perfil
EP01.mkv            Attack on Titan S1E1      [4]      [Auto]
EP02.mkv            Attack on Titan S1E2      [4]      [Auto]
EP03.mkv            Attack on Titan S1E3      [4]      [Auto]

[ GERAR LOTE ]
```

---

## Página Revisão

```text
12 SHORTS GERADOS

[▶] Short 01
Attack on Titan S1E1
47s

[ Aprovar ] [ Rejeitar ] [ Regenerar ]

[▶] Short 02
...
```

---

## Página Publicação

```text
SHORT                      DATA        HORA     METADATA   STATUS
Short 01                   06/10       11:00    ✓          Ready
Short 02                   06/10       14:00    ✓          Ready
Short 03                   06/10       18:00    …          Generating
Short 04                   06/10       21:00    ✕          Failed

[ AGENDAR APROVADOS ]
```

---

# 9. North Star

A experiência final deve ser:

```text
Selecionar episódios
        ↓
Escolher quantidade
        ↓
GERAR
        ↓
IA cria editorial
        ↓
Shortmaker edita
        ↓
Usuário revisa
        ↓
APROVAR
        ↓
IA cria metadata
        ↓
Agenda sugerida
        ↓
AGENDAR
```

O trabalho humano deve se concentrar em:

- escolha das fontes;
- avaliação criativa;
- aprovação.

Não em tarefas repetitivas de edição, render, metadata ou upload.

---

# 10. Critério de sucesso do produto

SHORTMAKER estará na visão final quando o usuário conseguir preparar aproximadamente um mês de conteúdo em uma única sessão, mantendo revisão humana antes da publicação e qualidade suficiente para que o resultado não pareça simples conteúdo automático em massa.
