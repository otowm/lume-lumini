# Graph Report - lume  (2026-08-01)

## Corpus Check
- 23 files · ~48,816 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 292 nodes · 551 edges · 26 communities (18 shown, 8 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Path
- Path
- Path

## God Nodes (most connected - your core abstractions)
1. `connect()` - 39 edges
2. `run()` - 25 edges
3. `compilerOptions` - 16 edges
4. `unit_state()` - 14 edges
5. `describe_video()` - 13 edges
6. `ollama_json()` - 12 edges
7. `Handoff: Lume — app de memória de tela & áudio` - 11 edges
8. `initialize()` - 10 edges
9. `atomic_write()` - 8 edges
10. `analyze_video_chapter()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `cancel_entire_queue()` --calls--> `connect()`  [EXTRACTED]
  app/backend/main.py → app/backend/database.py
- `cancel_pipeline()` --calls--> `connect()`  [EXTRACTED]
  app/backend/main.py → app/backend/database.py
- `cancel_queue_item()` --calls--> `connect()`  [EXTRACTED]
  app/backend/main.py → app/backend/database.py
- `cancel_video_analysis()` --calls--> `connect()`  [EXTRACTED]
  app/backend/main.py → app/backend/database.py
- `cancel_video_session()` --calls--> `connect()`  [EXTRACTED]
  app/backend/main.py → app/backend/database.py

## Import Cycles
- None detected.

## Communities (26 total, 8 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.10
Nodes (39): lifespan(), datetime, FastAPI, initialize(), adaptive_web_research(), analyze_video_chapter(), describe_long_video(), describe_screen() (+31 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (30): AnalysisTrace, api, Capture, DaySummary, HourSummary, QueueItem, QueueJob, RawFile (+22 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "Community 4"
Cohesion: 0.83
Nodes (4): get_storage_settings(), set_storage_settings(), storage_candidates(), storage_payload()

### Community 5 - "Community 5"
Cohesion: 0.24
Nodes (10): audio_file(), delete_capture(), delete_capture_file(), process_file(), ProcessFileRequest, safe_audio_path(), safe_screen_path(), screenshot() (+2 more)

### Community 6 - "Community 6"
Cohesion: 0.20
Nodes (10): capture_payload(), captures(), hourly_timeline(), search(), summary(), test_audio(), test_video_window(), VideoWindowTest (+2 more)

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "Community 8"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 9 - "Community 9"
Cohesion: 0.17
Nodes (13): cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_video_analysis(), cancel_video_session(), capture_action(), get_schedule(), run() (+5 more)

### Community 10 - "Community 10"
Cohesion: 0.22
Nodes (8): captura-dia, Estrutura instalada, Instalação e recuperação, Interface Lume, Intervalo ou mudança, Tela, Áudio, Índice e processamento noturno

### Community 12 - "Community 12"
Cohesion: 0.33
Nodes (6): generate_hourly_now(), generate_summary_now(), list_files(), list_videos(), pipeline_status(), unit_state()

### Community 13 - "Community 13"
Cohesion: 0.67
Nodes (6): load_loopback(), setup(), audio-bus.sh script, status(), unload_bus(), wait_pipewire()

### Community 14 - "Community 14"
Cohesion: 0.16
Nodes (22): atomic_write(), ContextUpdate, create_video_session(), directory_stats(), get_screen_settings(), get_sensitive_windows(), get_video_settings(), parse_shell_config() (+14 more)

### Community 15 - "Community 15"
Cohesion: 0.36
Nodes (6): game-video-loop script, cleanup(), finish_segment(), is_selected_app(), pause_background_captures(), resume_background_captures()

### Community 25 - "Path"
Cohesion: 0.23
Nodes (15): delete_file(), delete_video(), delete_video_session(), import_video(), list_video_sessions(), local_origin_only(), pipeline_queue(), preserve_video() (+7 more)

## Knowledge Gaps
- **65 isolated node(s):** `grava-audio.sh script`, `name`, `private`, `version`, `type` (+60 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Path` to `Community 0`, `Community 5`, `Community 6`, `Community 9`, `Community 12`, `Community 14`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `Community 0` to `Community 14`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `initialize()` connect `Community 0` to `Path`, `Community 12`, `Community 14`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **What connects `grava-audio.sh script`, `name`, `private` to the rest of the system?**
  _65 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.09877551020408164 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.0708245243128964 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.08695652173913043 - nodes in this community are weakly interconnected._