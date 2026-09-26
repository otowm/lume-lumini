# Revisão do Lume — experiência e contexto da IA

Data: 20/09/2026. Escopo: Meu Dia, busca, vídeos e sessões, captura/fila, ajustes e os caminhos que constroem o contexto para os modelos. Revisão do estado de trabalho atual, que já continha alterações locais anteriores.

O maior problema é a distância entre a experiência da pessoa e a organização técnica do sistema. Capturas, lotes e aplicativos são boas unidades de processamento, mas não equivalem necessariamente a atividades. “Assistir a Yomi no Tsugai” deve ser reconhecível sem ler uma sequência de análises de cenas. Essa distinção precisa existir tanto no contexto da IA quanto na apresentação.

## Melhorias aplicadas nesta revisão

| Área | Problema encontrado | Alteração |
|---|---|---|
| Atividades | Narrativas inteiras e todas as imagens competiam com o título; era necessário percorrer a lista para encontrar um assunto. | Busca por assunto, filtro de aplicativo, ordenação, descrição curta com expansão e quatro capturas iniciais por cartão. Texto maior e estados vazios específicos. |
| Atualização de atividades | Sessões antigas e novos grupos coexistiam, duplicando capturas. | Ao concluir o processamento, remove apenas grupos antigos cujas capturas estejam totalmente cobertas pelos atuais. Análises de mídia ausente ou parcialmente coberta são preservadas, inclusive na reanálise. |
| Duração | A diferença entre a primeira e a última captura aparecia como “cerca de X min”, sugerindo tempo contínuo de uso. | O cartão identifica o período como **intervalo observado**, sem transformá-lo em duração de uso. |
| Datas e busca | Uma consulta antiga podia terminar depois da nova e substituir seu conteúdo. | Verificação da seleção e da requisição atual antes de aplicar resultados; indicador de carregamento impede mostrar o conteúdo do dia anterior sob a nova data. Busca rápida e atualização da linha do tempo descartam respostas obsoletas. |
| Avisos | Erros de operações eram chamados de “Backend indisponível”; a consulta automática de status apagava o aviso. | Mensagem neutra com detalhe do erro, atualização explícita e botão para dispensar. A consulta automática não limpa erros de ações. |
| Janelas de configuração | O componente compartilhado não identificava o diálogo nem controlava foco ou Escape. | Nome acessível, foco inicial, circulação de Tab dentro da janela, fechamento por Escape e restauração do foco. Isso se aplica às telas que usam `Modal`; players e lightbox próprios ainda precisam de revisão equivalente. |
| Contexto visual do Qwen | Os lotes recebiam descrição anterior da IA, mas não o título original da janela. | Cada frame informa data/hora completa, janela capturada, título e descrição anteriores explicitamente identificados como inferência da IA, e áudio próximo. |
| Origem da fala | O texto sincronizado perdia a identificação da trilha. | A origem da fala acompanha o trecho quando existe nos segmentos; fontes ausentes continuam marcadas como não identificadas. |
| Instruções para o Qwen | Pedidos longos favoreciam narração de cenas e confusão entre personagem e usuário. | Prompts enfatizam a atividade da pessoa, continuidade entre episódios, mudanças reais de assunto, incertezas e separação entre fala de mídia e ações pessoais. Não exigem vários parágrafos para um conteúdo simples. |
| Consolidação de atividades | `json.dumps(analyses)[:60000]` cortava os últimos lotes e podia produzir JSON inválido. | Consolidação por grupos limitados e sucessivos. Todos os lotes participam; horários de início e fim são mantidos fora da inferência do modelo. Resumos intermediários têm limites explícitos. |

Arquivos centrais: [ActivitiesView.tsx](frontend/src/ActivitiesView.tsx), [main.tsx](frontend/src/main.tsx), [pipeline.py](app/backend/pipeline.py), [prompts.py](app/backend/prompts.py).

## Revisão das demais áreas e prioridades

### 1. Atividades por assunto, com agrupamento por aplicativo como apoio

A correção anterior estabilizou a identidade do aplicativo, mas um navegador ainda reúne anime, pesquisa e YouTube no mesmo grupo. O prompt agora recebe contexto para descrever essas transições; isso não cria sessões semânticas separadas no banco.

Próxima mudança recomendada: representar segmentos de assunto dentro da sessão, com evidências e horários, e permitir corrigir título, juntar e separar atividades. Não agrupar por semelhança de palavras apenas. Critério de aceitação: episódios consecutivos ficam juntos, uma pesquisa paralela continua identificável, e uma pausa longa permanece visível.

### 2. Contexto completo e verificável em resumos e vídeos

A consolidação de atividades foi corrigida. Ainda há cortes fixos em `generate_summary` (`activity_context[:50000]`) e `process_video_session` (`context[:50000]`). Dias ou sessões extensos podem perder o final. Os caminhos de vídeos já diferenciam contexto do usuário, evidência e inferência, o que vale preservar.

Próxima mudança: aplicar orçamento e síntese em níveis também nesses caminhos; incluir período e IDs das fontes. O tamanho em caracteres é apenas um limite operacional, não uma medida exata dos tokens do modelo.

Nos ajustes, o editor mostra o template; o inspetor da fila mostra a saída e métricas. Falta uma prévia fiel do **pedido final**: imagens selecionadas, intervalo da transcrição, instruções ativas, contexto manual e cortes aplicados. Essa prévia deve ser local e aberta sob demanda, com conteúdo sensível protegido pela mesma política dos registros.

### 3. Captura e fila: preservar o lugar de onde a pessoa veio

Corrigido nesta revisão: “Gerar resumo” e “Analisar atividades” mantêm a tela de origem, mostram processamento em andamento e oferecem “Ver processamento”. A tela consulta o andamento e atualiza os resultados ao concluir. O fluxo de atividades foi validado com submissão e conclusão simuladas, sem executar IA.

A fila mistura ações cotidianas e manutenção, como liberar VRAM. Separar as ações avançadas reduziria decisões desnecessárias. Cancelar processamento, remover da fila e excluir arquivo precisam ter efeitos e rótulos distintos. Há confirmações em ações destrutivas; preservar essa proteção.

### 4. Vídeos, áudio e busca: acesso consistente às evidências

A biblioteca já oferece botões de ação além do clique direito, capítulos e transcrição sincronizada. Nas miniaturas internas de sessão, algumas ações ainda dependem do clique direito/Shift+F10; adicionar um botão visível ajudaria no toque.

No resumo, os cartões de vídeo e sessão abrem, mas prints e áudios relevantes não têm a mesma ação. Unificar a abertura com os leitores já usados na busca. “Arquivo removido” deve continuar permitindo acesso à análise quando ela existe.

Busca precisa de um caminho claro para restringir período e de indicação consistente da quantidade de resultados. A busca rápida teve a concorrência corrigida, mas a relevância dos resultados não foi avaliada com um conjunto de consultas de referência.

### 5. Ajustes, calendário e acessibilidade

O calendário usa os dias retornados por `/api/days`, que representa registros processados. Um dia somente com capturas pendentes pode parecer inexistente. Separar indicadores de **capturado**, **processado** e **resumido** ajudaria a explicar essa diferença sem executar IA automaticamente.

Os controles de vídeo misturam mudanças salvas imediatamente e outras que dependem de salvar. Padronizar o comportamento e exibir alterações pendentes. Evitar que fechar a janela descarte silenciosamente uma edição de prompt.

A melhoria no componente `Modal` não cobre todos os overlays independentes. Estender o padrão para lightbox, player e busca rápida, incluindo leitura por tecnologia assistiva, nome dos botões, foco e retorno à origem. Conferir também contraste e tamanho dos controles menores em telas de toque.

## Validação e limites

- Testes de configuração/pipeline e prompts: 116 executados, 1 ignorado, sem falhas. Incluem contexto real de janela, separação de fontes, síntese de 20 lotes sem perder o último, JSON válido e caracteres escapados.
- Compilação TypeScript e build de produção executadas.
- Navegação em navegador real com registros de 17/09: busca e filtros de atividades, expansão de descrição, ajustes com teclado, linha do tempo, navegação principal e layout de 390 px sem overflow. Nenhum erro JavaScript. Também foram simulados erro persistente após consulta de status e respostas de datas fora de ordem; ambos passaram. Submissões de análise são simuladas; não inicia gravações nem apaga ou reprocessa os registros existentes.
- Os registros antigos não foram reprocessados nesta revisão. A reconciliação dos grupos duplicados acontece ao concluir a próxima análise com o código atualizado.
- As alterações de prompt só afetam novas análises. Prompts personalizados são preservados e não passam a usar automaticamente o novo texto padrão.
- Os testes verificam o contexto enviado e o fluxo do código. Não demonstram, sozinhos, melhoria factual do Qwen. Para medir essa qualidade, usar um conjunto pequeno de exemplos conhecidos: série com episódios consecutivos, troca de abas, fala paralela, jogo e sessão longa. Comparar identidade da atividade, atribuição da fala, continuidade e cobertura do fim da sessão.
