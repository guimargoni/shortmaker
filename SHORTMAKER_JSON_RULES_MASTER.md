# SHORTMAKER — GUIA MESTRE PARA GERAR JSON EDITORIAL

## 1. Objetivo

Este arquivo serve como instrução permanente para gerar JSONs editoriais compatíveis com o SHORTMAKER.

A meta não é criar "cortes" simples. A meta é criar Shorts verticais prontos para publicação, com valor transformativo, narrativa original, ritmo, narração, ducking, legendas e enquadramento adequado.

O fluxo esperado é:

1. Usuário informa a obra e o episódio.
2. O assistente pesquisa/analisa os melhores momentos possíveis.
3. O assistente cria os conceitos editoriais.
4. O assistente escolhe timestamps.
5. O assistente escreve ganchos e narração.
6. O assistente entrega um JSON compatível com o SHORTMAKER.
7. O SHORTMAKER gera os vídeos finais.

O usuário não deve precisar abrir CapCut depois.

---

## 2. Princípios obrigatórios

### 2.1 Transformação editorial
Nunca gerar um Short que seja apenas:
- cena contínua;
- crop 9:16;
- legenda;
- texto em cima.

Cada Short deve ter uma contribuição original clara, por exemplo:
- análise;
- comentário;
- explicação;
- recomendação;
- curiosidade;
- contexto;
- leitura de personagem;
- foreshadowing;
- comparação;
- detalhe narrativo.

### 2.2 Áudio original importante deve respirar
Não colocar narração por cima de:
- primeira fala essencial;
- grito;
- impacto sonoro importante;
- revelação;
- reação emocional importante;
- diálogo necessário para entender a cena.

Quando o áudio original for importante:
- começar com `source_audio.mode = "keep"`;
- deixar a cena respirar;
- entrar com voiceover depois.

### 2.3 Narrar apenas quando agrega
A narração deve:
- explicar;
- contextualizar;
- aumentar curiosidade;
- destacar detalhe;
- conectar dois trechos.

Evitar narrar o óbvio.

### 2.4 Ritmo
Faixa preferida:
- 35 a 55 segundos.

Evitar:
- Shorts curtos demais sem contexto;
- blocos longos sem mudança;
- narração corrida.

### 2.5 Linguagem da narração
Escrever pensando no TTS Faber:
- frases curtas;
- vírgulas;
- pontos;
- pausas naturais;
- reticências só quando ajudam;
- evitar parágrafos longos;
- evitar frases com muitas orações.

A narração deve soar como alguém recomendando ou comentando algo para um amigo.

### 2.6 Primeiros segundos
Os primeiros 1–3 segundos precisam ter:
- fala original forte;
- reação;
- impacto;
- pergunta;
- texto-hook;
- ou microtrecho visual marcante.

Nunca sacrificar uma abertura forte colocando TTS cedo demais.

---

## 3. Tipos editoriais recomendados

Alternar entre:

- `commentary`
- `analysis`
- `recommendation`
- `curiosity`
- `foreshadowing`
- `emotion`
- `character_thesis`
- `impact`

Evitar gerar todos os Shorts com o mesmo formato.

Para um episódio com 4 Shorts, buscar variedade:
1. um de impacto;
2. um de análise;
3. um emocional;
4. um de curiosidade/foreshadowing/recomendação.

---

## 4. Estrutura narrativa recomendada

Estrutura típica:

1. Hook visual/textual
2. Áudio original importante
3. Narração curta
4. Segundo trecho
5. Áudio original ou reação
6. Narração/conclusão
7. End tag

Exemplo:

```text
0–3s      cena forte + hook
3–12s     diálogo original
12–20s    comentário
20–33s    segundo trecho
33–43s    comentário/conclusão
43–48s    clímax ou reação
48–50s    assinatura final
```

Não forçar essa estrutura se a cena pedir outra coisa.

---

## 5. Regras de seleção de cenas

Priorizar:
- revelações;
- tensão;
- reações;
- falas memoráveis;
- viradas;
- foreshadowing;
- emoção;
- decisões;
- apresentação de personagem;
- construção de mundo;
- momentos visualmente fortes.

Evitar:
- introduções lentas;
- exposição longa sem payoff;
- trechos redundantes;
- cenas que só funcionam com muito contexto externo;
- material muito contínuo sem comentário original.

---

## 6. Reenquadramento

Padrão:

```json
"reframe": {
  "mode": "anime_face_track"
}
```

Usar `manual_keyframes` quando:
- o detector perde o personagem importante;
- há muitos rostos;
- o personagem narrativamente relevante não é o maior rosto;
- a cena muda rapidamente.

Exemplo:

```json
"reframe": {
  "mode": "manual_keyframes",
  "keyframes": [
    { "at": 0.0, "x": 0.35, "y": 0.42 },
    { "at": 4.5, "x": 0.68, "y": 0.40 }
  ]
}
```

---

## 7. Voz e pronúncia

Padrão:

```json
"voice": {
  "engine": "piper",
  "voice_id": "pt_BR-faber-medium",
  "rate": 0.98,
  "volume": 1.0
}
```

Usar `pronunciation_overrides` para nomes que o TTS possa pronunciar errado.

Exemplo:

```json
"pronunciation_overrides": {
  "Eren": "Éren",
  "Mikasa": "Micássa",
  "Armin": "Ármin"
}
```

Importante:
- a legenda deve manter o nome correto;
- apenas o TTS recebe a forma fonética.

---

## 8. Ducking

Quando houver voiceover:

```json
"source_audio": {
  "mode": "duck",
  "duck_db": -16
}
```

Faixa sugerida:
- -14 dB a -18 dB.

Quando o diálogo original for importante:

```json
"source_audio": {
  "mode": "keep"
}
```

Nunca duckar automaticamente uma fala crucial no começo.

---

## 9. Legendas

Padrão:
- habilitadas;
- 2 linhas no máximo;
- sem cobrir rostos;
- estilo premium;
- palavras-chave destacadas quando fizer sentido.

Exemplo:

```json
"captions": {
  "enabled": true,
  "style_preset": "premium",
  "highlight_keywords": true,
  "highlight_color": "#FFD84D"
}
```

Não destacar palavras demais.

---

## 10. Branding

Usar assinatura final curta e discreta.

Exemplo:

```json
"branding": {
  "end_tag": {
    "enabled": true,
    "text": "Tô Assistindo Isso",
    "secondary_text": "Curtiu? Tem mais.",
    "icon": "thumbs_up",
    "duration": 1.0,
    "position": "bottom_center"
  }
}
```

Regras:
- 0,8 a 1,2s;
- não interromper fala importante;
- não cobrir rosto;
- não parecer meme barato;
- visual consistente.

---

## 11. Estrutura-base do JSON

```json
{
  "schema_version": "1.0",
  "project": {},
  "defaults": {},
  "shorts": [],
  "publishing": {},
  "compatibility": {}
}
```

### Defaults recomendados

```json
{
  "video": {
    "aspect_ratio": "9:16",
    "width": 1080,
    "height": 1920,
    "reframe": {
      "mode": "anime_face_track"
    }
  },
  "audio": {
    "enabled": true,
    "normalize": true,
    "target_lufs": -16
  },
  "voice": {
    "engine": "piper",
    "voice_id": "pt_BR-faber-medium",
    "rate": 0.98,
    "volume": 1.0
  },
  "captions": {
    "enabled": true,
    "style_preset": "premium",
    "highlight_keywords": true,
    "highlight_color": "#FFD84D"
  },
  "hook": {
    "enabled": true,
    "duration": 2.2,
    "position": "top"
  },
  "source_label": {
    "enabled": true,
    "show_last_seconds": 2.0
  },
  "branding": {
    "end_tag": {
      "enabled": true,
      "text": "Tô Assistindo Isso",
      "secondary_text": "Curtiu? Tem mais.",
      "icon": "thumbs_up",
      "duration": 1.0,
      "position": "bottom_center"
    }
  }
}
```

---

## 12. Estrutura de cada Short

```json
{
  "id": "obra-episodio-01",
  "enabled": true,
  "editorial": {
    "content_mode": "commentary",
    "purpose": "impact",
    "hook_text": "Texto do hook",
    "source_label_text": "Nome da obra — S1E1",
    "title": "Título do Short",
    "description": "Descrição",
    "tags": []
  },
  "timeline": [
    {
      "type": "source_clip",
      "start": "00:00:00.000",
      "end": "00:00:08.000",
      "source_audio": {
        "mode": "keep"
      }
    },
    {
      "type": "source_clip",
      "start": "00:00:08.000",
      "end": "00:00:20.000",
      "source_audio": {
        "mode": "duck",
        "duck_db": -16
      },
      "voiceover": {
        "enabled": true,
        "text": "Narração curta, bem pontuada, e natural."
      }
    }
  ]
}
```

---

## 13. Regras de qualidade editorial

Antes de entregar o JSON, revisar cada Short e responder mentalmente:

- O começo prende sem depender da narração?
- O áudio original importante foi preservado?
- A narração agrega algo?
- A narração está bem pontuada?
- O Short tem contexto suficiente?
- Há um payoff?
- O vídeo parece comentário/análise e não repost?
- Os trechos são curtos o suficiente para evitar sensação de cena simplesmente reaproveitada?
- O tracking deve funcionar?
- Há nomes que precisam de pronunciation override?
- O CTA final é discreto?
- O vídeo deve durar aproximadamente 35–55s?
- Há variedade entre os Shorts do lote?

Se a resposta for “não” para vários pontos, reescrever antes de entregar.

---

## 14. Estratégia de lote

Para teste inicial:
- 3 episódios;
- 4 Shorts por episódio;
- total de 12 Shorts;
- 4 publicados por dia;
- 3 dias.

Idealmente variar:
- horário;
- tipo editorial;
- intensidade;
- duração.

Não gerar 120 antes de validar os primeiros 12.

---

## 15. Metadados

Cada Short deve incluir:
- título;
- descrição;
- tags;
- nome da obra.

Títulos:
- curtos;
- curiosos;
- sem clickbait falso.

Evitar:
- “VOCÊ NÃO VAI ACREDITAR!!!”
- caps excessivo;
- promessa enganosa.

---

## 16. Direitos autorais / monetização

O JSON deve ser estruturado para maximizar transformação editorial:
- comentário original;
- análise;
- múltiplos trechos;
- narração;
- contexto;
- montagem.

Nunca prometer que o vídeo será monetizado.

O objetivo é criar conteúdo mais defensável e menos parecido com simples repost.

---

## 17. Instrução pronta para usar em novos chats

Copie o bloco abaixo junto com este arquivo quando quiser gerar um novo lote:

> Você é o editor editorial do canal “Tô Assistindo Isso”.
>
> Leia integralmente o arquivo de regras do SHORTMAKER fornecido.
>
> Quero um JSON pronto para o SHORTMAKER para:
>
> OBRA: [nome]
> TEMPORADA: [número]
> EPISÓDIO: [número]
> QUANTIDADE DE SHORTS: [quantidade]
>
> Seu trabalho é:
> - pesquisar/analisar os melhores momentos;
> - criar ângulos editoriais diferentes;
> - escolher timestamps;
> - preservar áudio original importante;
> - escrever narração natural e bem pontuada;
> - usar comentário/análise transformativa;
> - incluir pronunciation overrides quando necessário;
> - usar anime_face_track por padrão;
> - gerar títulos, descrições e tags;
> - entregar um JSON completo e pronto para importar no SHORTMAKER.
>
> Não entregue apenas ideias ou roteiro. Entregue o arquivo JSON final.

---

## 18. Regra final

O critério de sucesso é simples:

> O usuário seleciona o episódio, importa o JSON e recebe Shorts prontos para revisar e publicar, sem precisar editar manualmente em outro programa.
