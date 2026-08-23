# Handoff: Lume — app de memória de tela & áudio

## Overview
Lume é um app pessoal (web/desktop) que grava continuamente **capturas de tela** e **gravações de áudio**, transcreve o áudio (Whisper / Qwen), faz OCR das telas, indexa tudo e permite **buscar em toda a memória** e ler **resumos automáticos** (diário/semanal/mensal). Inspirado no Screenpipe. Uso pessoal, single-user, foco em privacidade local.

Quatro áreas: **Busca** (tela principal), **Resumo do dia**, **Jogos** (tempo/progresso de jogo), **Linha do tempo**. Sidebar fixa com filtros rápidos e um bloco de status de captura/privacidade sempre visível.

## About the Design Files
O arquivo neste pacote (`Lume.dc.html`) é uma **referência de design feita em HTML** — um protótipo que mostra o visual e o comportamento pretendidos, **não** é código de produção pra copiar. A tarefa é **recriar este design no seu ambiente/stack** (você vai codar pelo Codex), usando os padrões da sua base. Os dados são todos mock; substitua pela captura/indexação real.

`Lume.dc.html` é um "Design Component": HTML + uma classe de lógica embutida. Abre direto no navegador. Você pode ignorar o formato e só ler o layout, os estilos inline e a lógica de estado como spec.

## Fidelity
**Alta fidelidade (hifi).** Cores, tipografia, espaçamento e interações são finais (design system Nocturne, abaixo). Recrie a UI fielmente com as libs da sua stack; os valores exatos estão em **Design Tokens**.

## Stack sugerida (não obrigatória)
App que lê tela + áudio pede um runtime com acesso ao SO. Sugestão comum: **Tauri ou Electron** (shell desktop) + **React + TypeScript** no front; **Rust ou Python** no backend de captura. Índice de busca: **SQLite FTS5** (busca full-text) ou similar. ASR: **Whisper** (rápido, trechos curtos) e **Qwen-Audio** (melhor em áudio ruidoso / PT). OCR das telas: Tesseract ou API nativa. Nada disso está no protótipo — é onde entra o seu código.

---

## Screens / Views

Layout global (todas as telas):
- Raiz `flex`, `height: 100vh`, `overflow: hidden`, fundo `#161826`, texto `#e9e9ed`, fonte Inter.
- **Sidebar** à esquerda: largura `244px`, `flex: none`, borda direita `1px` divider. Contém: logo, navegação (4 itens), "Filtros rápidos" (lista de apps por frequência), e no rodapé o bloco de status de captura + links de privacidade.
- **Main** à direita: `flex: 1`, coluna. Header fixo no topo (título + subtítulo + seletor de período segmentado Hoje/Semana/Mês à direita). Abaixo, área de conteúdo com scroll (`overflow-y: auto`, padding `16.8px`).
- Conteúdo de cada view é centralizado em `max-width: 940px`.

### Sidebar
- **Logo**: quadrado 26px, gradiente `135deg` de `--color-accent` → `--color-accent-700`, glow accent, ícone de "olho/alvo" (círculos concêntricos) em `--color-bg`. Ao lado, "Lume" em Inter 600, 18px.
- **Nav** (coluna, gap 2px): 4 botões — **Busca** (lupa), **Resumo do dia** (documento), **Jogos** (game controller), **Linha do tempo** (relógio). Ícones Phosphor 17px. Item ativo: fundo `color-mix(accent 16%)`, texto accent. Inativo: texto 78% opacidade. Hover: fundo `text 6%`. Padding `9px 10px`, radius 8px.
- **Filtros rápidos**: header "FILTROS RÁPIDOS" (uppercase, 10px, 45% opacidade). Lista dos 6 apps mais frequentes, cada linha: quadradinho de cor 8px (cor do app) + nome + contagem à direita. Clicar num app → vai pra Busca com aquele app como query.
- **Status de captura** (rodapé, `margin-top: auto`): card surface com sombra sm. Ponto 8px verde `#6ac89a` **pulsando** (keyframe `lumePulse`, opacity/scale, 1.8s) quando gravando; cinza estático quando pausado. Texto "Capturando"/"Captura pausada". Linha secundária: "4,2 GB usados" · "a cada 2s"/"em pausa". Botão secundário block "Pausar captura"/"Retomar captura". Abaixo, dois links texto 11px 50% opacidade: "Apps excluídos", "Apagar dados".

### 1. Busca (tela principal / default)
- **Propósito**: buscar em tudo que foi capturado (telas + áudio).
- **Header**: título "Busca na memória", subtítulo "N capturas indexadas hoje/no período".
- **Barra de busca**: largura total, altura 50px, fundo surface, borda divider, radius 8px, lupa Phosphor 18px absoluta à esquerda (padding-left 44px), fonte 16px, `caret-color: --color-accent`. Placeholder "Buscar em tudo que você viu e ouviu…".
- **Linha de filtros**: controle segmentado **Tudo / Telas / Áudio** (filtra por tipo). À direita do seg, label de contagem ("N resultados para "query"" ou "N capturas"). Botão ghost "Limpar busca" (só visível com query).
- **Feed de resultados** (coluna, gap 8.4px). Cada card:
  - Linha `flex`, gap 11.2px, padding 8.4px, borda `1px` divider, radius 8px, fundo `color-mix(surface 55%)`. Hover: borda accent 45%, fundo surface cheio, cursor pointer.
  - **Thumbnail** 96×66px, radius 4px: gradiente `140deg` da cor do app → bg, borda interna sutil da cor do app. Glyph = 2 letras do app (Inter 600) ou "▮▮" pra áudio. Áudio mostra badge de duração no canto inferior direito.
  - **Conteúdo**: tag de tipo (`Tela` neutra / `Áudio` accent) + meta "HH:MM · App"; título Inter 500 15px; snippet do texto (OCR/transcrição) com `-webkit-line-clamp: 2`; linha de tags neutras 10px.
- **Estado vazio**: quando 0 resultados, lupa grande + "Nada encontrado para "query"" + dica.
- **Busca**: filtra por tipo E por termos (todos os termos precisam bater em app+título+texto+tags, lowercase). Resultados em ordem cronológica reversa.

### 2. Resumo do dia
- **Propósito**: leitura rápida do que aconteceu no período.
- **Header**: "Resumo do dia" · "Segunda, 20 de julho · gerado às 18:05".
- Seções (coluna, gap 22.4px):
  1. **O que você fez** — título com ícone de "brilho" accent; card surface com 1–2 parágrafos de narrativa (gerada por LLM a partir das capturas do dia).
  2. **Blocos de tempo por app** — barras horizontais: label do app (96px), trilho `text 6%` altura 22px radius 5px, barra preenchida gradiente accent proporcional aos minutos, duração à direita (tabular-nums).
  3. **Tarefas detectadas** — lista; cada linha: checkbox (18px, radius 5px; feito = fundo accent + ✓; pendente = borda neutra), texto (riscado + 45% se feito), origem à direita ("Gmail · 08:42"). Extraídas de telas/conversas.
  4. **Reuniões transcritas** — grid 2 colunas de cards: tag "Áudio", meta "HH:MM · duração · app", título, snippet em itálico entre aspas, rodapé "Transcrito com Whisper/Qwen".
  5. **Momentos-chave** — linha de thumbnails 196×118px (mesmo estilo do feed) com título + meta embaixo.

### 3. Jogos
- **Propósito**: acompanhar tempo e progresso em jogos (subconjunto do tempo-por-app, especializado).
- **Header**: "Jogos" · "Progresso e tempo de jogo detectados automaticamente".
- Seções (gap 22.4px):
  1. **Faixa de métricas** — grid 4 colunas de cards surface: label uppercase 11px + valor grande Inter 600 22px + sub. (Tempo na semana, Mais jogado, Sessão média, Melhor dia.)
  2. **Seus jogos** — grid 2 colunas de cards (padding 11.2px, gap 8.4px):
     - **Capa** 100%×96px: gradiente `140deg` da cor do jogo → bg, borda interna; glyph = iniciais (ex. "ER", "BG").
     - Título Inter 500 17px + gênero à direita (50% opacidade).
     - **Progresso**: label "Progresso" + "%" accent; trilho `text 8%` 7px radius 99px; barra gradiente da cor do jogo → accent.
     - Trio de stats: Tempo total / Esta semana (accent) / Conquistas (x/y), tabular-nums.
     - Rodapé (borda-topo divider): "Jogado ontem" · tendência ("+2h10 vs. semana passada").
  3. **Horas por dia** (coluna esquerda, grid `1fr 1.3fr`) — card surface com mini bar-chart: 7 barras (Seg–Dom), altura proporcional às horas, gradiente accent vertical; dias sem jogo = barrinha neutra 2px. Label do dia embaixo.
  4. **Sessões recentes** (coluna direita) — lista; cada linha: ícone em quadrado accent-tint (troféu = conquista/chefe, bandeira = marco, mapa = exploração), quadradinho de cor do jogo + nome + quando, "momento detectado" abaixo, duração à direita. Ex.: "Derrotou Margit, o Presságio Caído", "Conquista desbloqueada: Alma Pura".
- **Origem dos dados**: detectar jogo em foco (nome do processo/janela), somar tempo de sessão, e detectar "momentos" via OCR de telas de conquista/level-up/chefe.

### 4. Linha do tempo
- **Propósito**: tudo que aconteceu, em ordem cronológica.
- **Header**: "Linha do tempo" · "Tudo que aconteceu, em ordem".
- Coluna `max-width: 720px`. Linha vertical à esquerda (gradiente que some nas pontas, 2px). Cada evento:
  - Marcador circular 14px na linha (borda = accent se áudio, neutra se tela).
  - Conteúdo: hora (tabular-nums, accent-300) + tag de tipo + app; título abaixo.
  - **Miniatura de referência** à direita (tamanho controlável via tweak, padrão 120px, aspect ~1.65:1), mesmo estilo de thumb do feed. **Clicável**: leva pra Busca filtrada por aquele app ("Ver mais neste contexto"). Hover na linha: fundo surface + CTA "Ver mais neste contexto →" aparece.
  - **Tweaks**: `timelineThumbs` (bool, mostrar/ocultar miniaturas) e `thumbSize` (72–180px). No app real, exponha como preferências.

---

## Interactions & Behavior
- **Navegação**: state `view` ('busca'|'resumo'|'jogos'|'timeline'); clicar no nav troca. Header (título/subtítulo) muda por view.
- **Período**: state `period` ('hoje'|'semana'|'mês'); segmentado no header. No protótipo afeta só labels — no app real deve refiltrar dados e resumos.
- **Busca**: `query` atualiza no `input` (live), `type` no segmentado; resultados filtrados em memória. Filtro rápido de app (sidebar) e clique em miniatura da timeline setam `view='busca'` + `query=app`.
- **Captura**: `paused` alterna via botão; controla o ponto pulsante e os labels de status.
- **Hover states**: cards de resultado (borda/fundo accent), botões de nav (fundo), linhas da timeline (fundo + revelar CTA). Todas as transições ~120–150ms.
- **Foco de teclado**: anel `2px solid --color-accent`, offset 2px (`:focus-visible`) — nunca o azul padrão.

## State Management
- `view: string` — aba ativa.
- `period: string` — hoje/semana/mês (deve disparar refetch/reagg no app real).
- `query: string`, `type: 'tudo'|'screen'|'audio'` — estado da busca.
- `paused: boolean` — captura ligada/pausada (deve iniciar/parar o pipeline real).
- Preferências: `timelineThumbs: boolean`, `thumbSize: number`.
- **Dados (mock no protótipo, reais no app)**: `captures[]` (id, time, type screen|audio, app, title, text[OCR/transcrição], tags[], duration?, model?), agregados de resumo (narrativa, blocos de tempo, tarefas, reuniões, momentos), e dados de jogos (jogo, tempo total/semana, sessões, progresso%, conquistas, momentos).

## Design Tokens (Nocturne)
Tema **escuro, azul-acinzentado, denso (densidade 0.7×), radius 8px**. Accent blurple usado como linha/glow, nunca como preenchimento grande.

**Cores**
- Fundo `--color-bg: #161826` · Surface `--color-surface: #232532` · Texto `--color-text: #e9e9ed`
- Divider `color-mix(#e9e9ed 16%, transparent)`
- Accent `--color-accent: #9184d9`. Ramp accent: 100 `#f5f4ff` · 300 `#d2cefd` · 400 `#b5abfc` · 500 `#968ae0` · 600 `#796cbf` · 700 `#5d5294` · 800 `#423a6a` · 900 `#2b2741`. (Texto accent em corpo → use accent-300.)
- Neutros: 100 `#f3f5fe` · 400 `#b2b6ca` · 500 `#9397ab` · 600 `#75798c` · 700 `#595d6c` · 800 `#3f424d` · 900 `#292b31`.
- Sucesso/gravando: `#6ac89a`.
- Cores de app (tints de thumbnail): Gmail `#c86a6a`, VS Code `#6a8fc8`, Figma `#c88a5a`, Chrome `#6ac89a`, Notion `#b0b4c8`, Slack `#a87ac8`, Terminal `#8a8f9c`; áudio (Meet/Zoom/Gravador) usa accent.
- Cores de jogo: Elden Ring `#c8a15a`, Baldur's Gate 3 `#9a7ac8`, Hollow Knight `#5ab8c8`, Stardew Valley `#7ac88a`.

**Tipografia**: Inter (headings peso 500, nunca mais pesado; body 400). Escala: h4 20px, título de card 17px, corpo 15px, secundário 13px, meta 11–12px. Line-height base 1.55, headings 1.12, letter-spacing headings -0.015em.

**Espaçamento** (`--space-*`, densidade 0.7×): 1 = 2.8px · 2 = 5.6px · 3 = 8.4px · 4 = 11.2px · 6 = 16.8px · 8 = 22.4px.

**Radius**: sm 4px · md 8px · lg 14px.

**Sombras** (fundo escuro = borda + escuridão ambiente, nunca sombra pesada): sm `0 0 0 1px #3f424d` · md `0 0 0 1px #595d6c, 0 6px 18px rgba(0,0,0,.55)` · lg `0 0 0 1px #9397ab, 0 16px 40px rgba(0,0,0,.65)`.

**Regras/divisores**: linhas somem nas pontas (gradiente pra transparente ~48px de cada lado), não param secas.

## Assets
- **Ícones**: Phosphor (https://phosphoricons.com), inline SVG em `currentColor`, viewBox 256. Usados: lupa, documento, game-controller, relógio, troféu, bandeira, mapa, brilho, seta.
- **Miniaturas/capas**: no protótipo são placeholders (gradiente da cor + iniciais). No app real, use os screenshots reais das capturas / capas dos jogos.
- **Fonte**: Inter via Google Fonts.
- **Design system**: Nocturne (stylesheet + tokens no protótipo). Recrie os tokens acima na sua base.

## Files
- `Lume.dc.html` — protótipo completo (todas as 4 views + sidebar + lógica de estado). Fonte de verdade da UI.
