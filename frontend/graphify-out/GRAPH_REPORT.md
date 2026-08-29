# Graph Report - frontend  (2026-08-29)

## Corpus Check
- 5 files · ~8,306 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 135 nodes · 185 edges · 9 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `da259cb6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.tsx
- api.ts
- compilerOptions
- package.json
- devDependencies
- videoTime
- lib
- uploadVideo

## God Nodes (most connected - your core abstractions)
1. `compilerOptions` - 16 edges
2. `videoTime()` - 10 edges
3. `App()` - 9 edges
4. `scripts` - 4 edges
5. `sessionDuration()` - 4 edges
6. `VoiceIdentityPanel()` - 4 edges
7. `CustomVideoPlayer()` - 4 edges
8. `lib` - 4 edges
9. `uploadVideo()` - 3 edges
10. `canonicalGameName()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `App()` --calls--> `uploadVideo()`  [EXTRACTED]
  src/main.tsx → src/api.ts

## Import Cycles
- None detected.

## Communities (9 total, 0 thin omitted)

### Community 0 - "main.tsx"
Cohesion: 0.07
Nodes (12): CAPTION_LABELS, CAPTION_ORDER, CapturaTab, dayViews, EditableVideoSpeaker, gameCovers, icons, labels (+4 more)

### Community 1 - "api.ts"
Cohesion: 0.05
Nodes (35): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, Capture, CleanupSettings, DaySummary (+27 more)

### Community 2 - "compilerOptions"
Cohesion: 0.09
Nodes (22): DOM, DOM.Iterable, ES2022, src, compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop (+14 more)

### Community 3 - "package.json"
Cohesion: 0.14
Nodes (13): dependencies, react, react-dom, name, private, scripts, build, dev (+5 more)

### Community 4 - "devDependencies"
Cohesion: 0.22
Nodes (9): devDependencies, @types/react, @types/react-dom, typescript, vite, @types/react, @types/react-dom, typescript (+1 more)

### Community 5 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 6 - "lib"
Cohesion: 0.67
Nodes (3): SessionCard(), sessionDuration(), SessionViewer()

### Community 7 - "uploadVideo"
Cohesion: 0.33
Nodes (7): uploadVideo(), analysisAverage(), App(), canonicalGameName(), groupCaptures(), queueEta(), sessionGameName()

## Knowledge Gaps
- **51 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+46 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `devDependencies` connect `devDependencies` to `package.json`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _51 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06896551724137931 - nodes in this community are weakly interconnected._
- **Should `api.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.05405405405405406 - nodes in this community are weakly interconnected._
- **Should `compilerOptions` be split into smaller, more focused modules?**
  _Cohesion score 0.08695652173913043 - nodes in this community are weakly interconnected._
- **Should `package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._