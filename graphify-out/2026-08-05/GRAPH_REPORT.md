# Graph Report - lume  (2026-08-05)

## Corpus Check
- 32 files · ~28,649 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 409 nodes · 793 edges · 23 communities (15 shown, 8 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 7
- Community 8
- Community 10
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 20
- Community 21
- Path
- Path
- install-captura-dia.sh

## God Nodes (most connected - your core abstractions)
1. `connect()` - 45 edges
2. `run()` - 28 edges
3. `WindowsCaptureBackend` - 19 edges
4. `CaptureBackend` - 17 edges
5. `LinuxCaptureBackend` - 16 edges
6. `compilerOptions` - 16 edges
7. `Monitor` - 15 edges
8. `unit_state()` - 14 edges
9. `describe_video()` - 14 edges
10. `AudioConfig` - 14 edges

## Surprising Connections (you probably didn't know these)
- `delete_video_marker()` --calls--> `connect()`  [EXTRACTED]
  app/backend/main.py → app/backend/database.py
- `discover()` --calls--> `connect()`  [EXTRACTED]
  app/backend/pipeline.py → app/backend/database.py
- `generate_hourly_summaries()` --calls--> `connect()`  [EXTRACTED]
  app/backend/pipeline.py → app/backend/database.py
- `generate_summary()` --calls--> `connect()`  [EXTRACTED]
  app/backend/pipeline.py → app/backend/database.py
- `process_pending()` --calls--> `connect()`  [EXTRACTED]
  app/backend/pipeline.py → app/backend/database.py

## Import Cycles
- None detected.

## Communities (23 total, 8 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.10
Nodes (44): initialize(), adaptive_web_research(), analyze_video_chapter(), describe_long_video(), describe_screen(), describe_video(), discover(), extract_adaptive_keyframes() (+36 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (31): AnalysisTrace, api, Capture, DaySummary, HourSummary, QueueItem, QueueJob, RawFile (+23 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (38): ABC, AudioConfig, CaptureBackend, matched_sensitive_pattern(), Monitor, Path, Interface comum de captura, independente de sistema operacional.  Cada SO fornec, Monitor que contém a janela em foco, se determinável. (+30 more)

### Community 5 - "Community 5"
Cohesion: 0.14
Nodes (13): 1. Pré-requisitos, 2. Obter o projeto, 3. Ambiente Python, 4. Rodar o self-test de captura, 5. Se a saída do sistema NÃO for capturada, 6. O que ainda NÃO funciona no Windows, 7. Reportar o resultado, Como ler o resultado do áudio (+5 more)

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "Community 8"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 10 - "Community 10"
Cohesion: 0.22
Nodes (8): captura-dia, Estrutura instalada, Instalação e recuperação, Interface Lume, Intervalo ou mudança, Tela, Áudio, Índice e processamento noturno

### Community 13 - "Community 13"
Cohesion: 0.67
Nodes (6): load_loopback(), setup(), audio-bus.sh script, status(), unload_bus(), wait_pipewire()

### Community 14 - "Community 14"
Cohesion: 0.06
Nodes (98): connect(), row_dict(), atomic_write(), audio_file(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_video_analysis() (+90 more)

### Community 15 - "Community 15"
Cohesion: 0.31
Nodes (6): game-video-loop script, cleanup(), finish_segment(), is_selected_app(), pause_background_captures(), resume_background_captures()

## Knowledge Gaps
- **75 isolated node(s):** `grava-audio.sh script`, `name`, `private`, `version`, `type` (+70 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Community 14` to `Community 0`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `initialize()` connect `Community 0` to `Community 14`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `WindowsCaptureBackend` (e.g. with `AudioConfig` and `CaptureBackend`) actually correct?**
  _`WindowsCaptureBackend` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `CaptureBackend` (e.g. with `LinuxCaptureBackend` and `WindowsCaptureBackend`) actually correct?**
  _`CaptureBackend` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `grava-audio.sh script`, `name`, `private` to the rest of the system?**
  _75 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.10202655485674354 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06382978723404255 - nodes in this community are weakly interconnected._