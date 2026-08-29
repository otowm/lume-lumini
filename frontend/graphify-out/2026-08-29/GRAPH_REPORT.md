# Graph Report - frontend  (2026-08-06)

## Corpus Check
- 5 files · ~4,999 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 98 nodes · 119 edges · 9 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

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
2. `scripts` - 4 edges
3. `videoTime()` - 4 edges
4. `lib` - 4 edges
5. `uploadVideo()` - 3 edges
6. `CustomVideoPlayer()` - 3 edges
7. `App()` - 3 edges
8. `react` - 2 edges
9. `react-dom` - 2 edges
10. `@types/react` - 2 edges

## Surprising Connections (you probably didn't know these)
- `App()` --calls--> `uploadVideo()`  [EXTRACTED]
  src/main.tsx → src/api.ts

## Import Cycles
- None detected.

## Communities (9 total, 0 thin omitted)

### Community 0 - "main.tsx"
Cohesion: 0.09
Nodes (8): QueueItem, QueueJob, VideoChapter, VideoFile, icons, labels, Panel, View

### Community 1 - "api.ts"
Cohesion: 0.10
Nodes (19): AnalysisTrace, api, AudioEvent, Capture, DaySummary, HourSummary, RawFile, ScheduleSettings (+11 more)

### Community 2 - "compilerOptions"
Cohesion: 0.11
Nodes (18): src, compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx (+10 more)

### Community 3 - "package.json"
Cohesion: 0.14
Nodes (13): dependencies, react, react-dom, name, private, scripts, build, dev (+5 more)

### Community 4 - "devDependencies"
Cohesion: 0.22
Nodes (9): devDependencies, @types/react, @types/react-dom, typescript, vite, @types/react, @types/react-dom, typescript (+1 more)

### Community 5 - "videoTime"
Cohesion: 0.40
Nodes (5): AudioAnalysis(), chapterStart(), CustomVideoPlayer(), videoTime(), VideoViewer()

### Community 6 - "lib"
Cohesion: 0.50
Nodes (4): DOM, DOM.Iterable, ES2022, lib

### Community 7 - "uploadVideo"
Cohesion: 0.67
Nodes (3): uploadVideo(), App(), groupCaptures()

## Knowledge Gaps
- **41 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+36 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `compilerOptions` connect `compilerOptions` to `lib`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `devDependencies` connect `devDependencies` to `package.json`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._
- **Should `api.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.09523809523809523 - nodes in this community are weakly interconnected._
- **Should `compilerOptions` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._