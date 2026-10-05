# SHORTMAKER — MVP FINAL PLAN (ENXUTO)

## Ponto de partida
Assumir M0–M3.3 como PASS.
Não reescrever renderer, TTS, tracking, captions, ducking ou branding já existentes.
Se M3.4 ainda não foi implementado, NÃO executar a spec antiga inteira: incorporar apenas o polimento essencial descrito no M4 abaixo.

## O que fica FORA do MVP
- IA editorial automática
- Character Storytelling
- Analytics avançado
- SQLite/servidor/cloud
- múltiplos usuários
- publicação em outras redes
- aprendizado automático
- clonagem de voz
- catálogo musical complexo

A análise editorial continua sendo feita manualmente via JSON.

---

# M4 — PREMIUM POLISH + MUSIC
Objetivo: melhorar drasticamente o acabamento sem aumentar muito a complexidade.

### Implementar
1. Música local por estilo:
   - `action`
   - `tension`
   - `emotional`
   - `none`
2. Estrutura esperada:
   - `music/action/`
   - `music/tension/`
   - `music/emotional/`
3. JSON:
```json
"music": {
  "enabled": true,
  "style": "action"
}
```
4. Seleção:
   - escolher aleatoriamente um arquivo válido da pasta;
   - evitar repetir a última faixa usada quando houver alternativa;
   - MP3/M4A/WAV aceitos.
5. Mix:
   - música sempre abaixo de fala;
   - ducking durante diálogo/narração;
   - fade-in/fade-out curto;
   - loop/corte automático até duração final.
6. Captions premium:
   - branco;
   - contorno preto;
   - palavra ativa em amarelo quando word timing estiver disponível;
   - máximo 2 linhas;
   - preservar compatibilidade com captions existentes.
7. Polimento mínimo:
   - manter `anime_face_track`;
   - punch-in/slow zoom somente se já houver infraestrutura simples;
   - não criar um novo motor de efeitos;
   - não adicionar efeitos chamativos.

### PASS
- JSON antigo continua funcionando;
- vídeo sem música funciona;
- cada um dos 3 estilos funciona;
- música não cobre diálogo;
- última faixa não repete quando houver alternativa;
- captions atuais não regrediram;
- 1080x1920 preservado;
- testes anteriores continuam PASS.

### NÃO FAZER
IA, YouTube, queue avançada, analytics, banco de dados, refactor grande.

---

# M5 — PRODUCTION + REVIEW + METADATA
Objetivo: deixar o programa utilizável em lote sem IA editorial.

### Tela/fluxo
`PRODUÇÃO -> REVIEW -> PUBLICAÇÃO`

### Produção
Permitir adicionar vários itens.
Cada item:
- source video
- editorial JSON
- media name
- output folder
- status

Botões:
- `Adicionar`
- `Gerar`
- `Gerar fila`

Processamento sequencial. Um erro não bloqueia os próximos.

### Review
Para cada Short renderizado:
- arquivo
- preview/abrir
- duração
- título
- status
- `Aprovar`
- `Rejeitar`
- `Regenerar`
- `Publicar` somente quando aprovado

### Título
Sem IA no MVP.
O JSON editorial fornece o hook/título base e o nome da mídia.

Formato final obrigatório:
`<hook chamativo> <emoji> | <nome da mídia>`

Exemplo:
`Essa confissão muda tudo 😢 | Attack on Titan`

Regras:
- 1 emoji;
- sem nomes técnicos de arquivo;
- sem `s01e02_01`;
- título editável antes de publicar.

### Persistência
Somente JSON local.
Salvar:
- fila
- status
- títulos editados
- aprovação
- output
- publicação pendente/concluída

Sem SQLite.

### PASS
- 3 fontes + 3 JSONs podem ser colocados na fila;
- render sequencial;
- falha isolada;
- review funcional;
- aprovação persistida;
- título formatado;
- reiniciar app não perde fila/status.

---

# M6 — YOUTUBE SMART PUBLISHER
Objetivo: conectar o canal e automatizar upload + agendamento.

### Configuração
Tela simples:
- `Conectar YouTube`
- timezone padrão: `America/Sao_Paulo`
- 4 horários configuráveis
- defaults:
  - 11:00
  - 14:00
  - 18:00
  - 21:00

Persistir configurações localmente.

### OAuth
Usar API oficial do YouTube.
Credenciais externas:
- Google account
- YouTube channel
- Google Cloud project
- YouTube Data API v3
- OAuth 2.0 Desktop Client JSON

Nunca commitar segredo/token.

### Scheduler
Ao clicar `Publicar`:
1. procurar o primeiro slot futuro livre;
2. se os 4 slots do dia estiverem ocupados, avançar para o próximo dia;
3. marcar localmente como `RESERVED_PENDING`;
4. fazer upload/agendamento;
5. somente após resposta de sucesso com `video_id` e horário confirmado:
   - marcar `SCHEDULED`;
   - ocupar o slot;
6. se falhar:
   - marcar `FAILED`;
   - liberar o slot.

Estados:
- `FREE`
- `RESERVED_PENDING`
- `SCHEDULED`

### Regras
- horário passado hoje nunca é usado;
- dois Shorts nunca podem ocupar o mesmo slot;
- retry reutiliza um slot válido;
- publicação exige Short aprovado;
- app não escolhe conteúdo sozinho.

### Dashboard mínimo
Mostrar:
- próximo slot livre;
- quantos Shorts estão agendados;
- quantos dias completos de conteúdo existem;
- falhas;
- lista simples de slots próximos.

Exemplo:
```
05/10  11:00 ✅ 14:00 ✅ 18:00 ✅ 21:00 ✅
06/10  11:00 próximo | 14:00 livre | 18:00 livre | 21:00 livre
Cobertura: 1 dia completo
```

### PASS
- OAuth real funciona;
- upload real de 1 Short funciona;
- horário só fica ocupado após sucesso;
- falha libera slot;
- segundo Short pega próximo horário;
- após 4 slots, quinto vai ao dia seguinte;
- título final correto;
- status sobrevive ao restart;
- nenhuma regressão no render.

### BLOCKED_EXTERNAL aceitável
Se a API/conta exigir verificação/auditoria externa para publicação pública/agendada:
- marcar somente a integração externa como `BLOCKED_EXTERNAL`;
- preservar todo o restante como PASS;
- reportar exatamente o requisito externo.
Não reinventar workaround.

---

# MVP DONE
MVP está concluído quando:

1. usuário coloca vídeo + JSON editorial;
2. Shortmaker renderiza;
3. música/polimento são aplicados automaticamente;
4. usuário assiste;
5. usuário aprova;
6. usuário clica `Publicar`;
7. Shortmaker gera título final;
8. escolhe próximo dos 4 horários;
9. envia/agende no YouTube;
10. registra o slot somente após sucesso;
11. mostra quantos dias de conteúdo já estão cobertos.

A única etapa manual fora do app continua sendo a criação do JSON editorial.

---

# PROMPT CURTO PARA CODEX — M4

Implemente somente o milestone M4 — PREMIUM POLISH + MUSIC do plano do MVP.

Preserve integralmente M0–M3.3. Não faça refactor amplo. Não implemente IA, YouTube, analytics, SQLite ou features de M5/M6.

Requisitos:
- `music.style`: action/tension/emotional/none;
- pastas locais `music/<style>/`;
- seleção aleatória;
- evitar repetir a última faixa quando houver alternativa;
- MP3/M4A/WAV;
- loop/corte automático;
- fade curto;
- ducking sob diálogo/narração;
- captions: branco + contorno preto + palavra ativa amarela quando houver word timing;
- preservar anime_face_track, Faber, branding e 1080x1920;
- JSON antigo deve continuar funcionando.

Não crie um motor novo de efeitos. Reutilize infraestrutura existente.

Execute testes existentes + testes mínimos novos.
Faça um smoke real.
Ao terminar, pare e reporte:
- M4 PASS/BLOCKED
- total de testes
- arquivos alterados
- output do smoke
- limitações
- regressões
Não inicie M5.

---

# PROMPT CURTO PARA CODEX — M5

M4 está PASS. Implemente somente M5 — PRODUCTION + REVIEW + METADATA.

Preserve renderer e M4. Sem IA editorial, YouTube, analytics, SQLite ou refactor amplo.

Implementar:
- fila local de múltiplos itens: source video + editorial JSON + media name + output;
- processamento sequencial;
- falha de um item não bloqueia o próximo;
- persistência em JSON local;
- Review de Shorts renderizados com Abrir/Preview, Aprovar, Rejeitar, Regenerar;
- botão Publicar visível/habilitado apenas para aprovado;
- título editável;
- título padrão: `<hook> <1 emoji> | <media name>`;
- remover identificadores técnicos do título.

Testes mínimos + todos anteriores.
Ao terminar, pare e reporte M5 PASS/BLOCKED.
Não inicie M6.

---

# PROMPT CURTO PARA CODEX — M6

M5 está PASS. Implemente somente M6 — YOUTUBE SMART PUBLISHER.

Não alterar renderer.

Implementar:
- OAuth 2.0 Desktop oficial do YouTube;
- configuração local de timezone + 4 horários;
- defaults America/Sao_Paulo: 11:00, 14:00, 18:00, 21:00;
- botão Publicar para Short aprovado;
- cálculo automático do próximo slot futuro livre;
- estados FREE / RESERVED_PENDING / SCHEDULED;
- ocupar slot somente após sucesso da API;
- liberar slot em falha;
- depois de 4 slots, avançar ao próximo dia;
- persistir video_id, publish_at, status e erro;
- retry seguro;
- dashboard mínimo de slots/cobertura em dias;
- credenciais/tokens fora do Git.

Faça teste unitário do scheduler antes do OAuth real.
Depois faça smoke real com 1 Short.
Se houver requisito externo de auditoria/verificação da API, marque BLOCKED_EXTERNAL e reporte exatamente a exigência; não invente workaround.

Ao terminar, pare. Não implemente analytics nem IA editorial.
