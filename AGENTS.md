## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Lumini (modo gravador)

O projeto é instalado em dois modos: `completo` (com IA) e `lumini` (só o
gravador). Ao acrescentar uma rota nova em `app/backend/main.py`, classifique-a:
se depende do pipeline/Ollama, ela entra em `_PREFIXOS_IA`/`_SUFIXOS_IA`; se é de
gravação, entra na lista de `test_toda_rota_da_api_esta_classificada`. O teste
falha enquanto a rota não estiver em um dos dois lados — de propósito, para o
modo não apodrecer.

Nada em `app/capture/` pode importar `pipeline` ou `audio_intelligence`, e nada
no caminho da API pode importar `numpy`/`sherpa-onnx` no topo do módulo: o Lumini
não instala essas dependências, e `test_api_sobe_sem_numpy_e_sem_sherpa` tranca
isso.
