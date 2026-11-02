## Context

A base do sistema já possui autenticação por perfil, gestão de produtos, vendas e funcionários. O passo seguinte é consolidar a operação em um painel do gestor, sem criar novos registros ou rotas de escrita indiscriminadas.

## Goals / Non-Goals

**Goals:**

- Entregar uma visão operacional do gestor no Reflex.
- Exibir métricas de vendas e estoque crítico com dados já persistidos.
- Restringir o acesso ao perfil gestor e preservar a autorização no backend.
- Reaproveitar o dado de produtos, vendas, item de pedido e funcionários sem duplicação de regras.

**Non-Goals:**

- Não implementar edição de vendas, produtos ou funcionários pelo painel.
- Não criar relatórios financeiros complexos, filtros avançados ou gráficos analíticos sofisticados.
- Não incluir dados pessoais sensíveis como salário na tela principal do painel.
- Não abrir acesso do colaborador ao dashboard.

## Decisions

### Dashboard para leitura e agregação

A principal fonte de verdade será a camada de leitura do Xano, com consultas agregadas e filtros por dia ou período. A alternativa de montar todo o relatório no frontend foi rejeitada porque exigiria duplicar a lógica de negócio e romperia a separação entre regra e visão.

### Dados mínimos e sem duplicação

Os cards principais devem usar a mesma base já existente:

- total de vendas do dia ou período;
- quantidade de itens vendidos por medicamento;
- quantidade de funcionários ativos;
- produtos abaixo do estoque mínimo.

### Autorização derivada da sessão

A sessão autenticada identifica perfil. O dashboard será acessível somente ao gestor, com 401 para sessão inválida e 403 para perfil sem permissão.

### Interface simples e verificável

A tela deve ser direta: resumos em cards, tabela de reposição e ranking de medicamentos mais vendidos. O foco é entregar valor operacional ao gestor em uma página clara, deixando refinamentos visuais para mudanças posteriores.

## Risks / Trade-offs

- **[Agregação em tempo real]** → as consultas devem ser simples, read-only e conversão clara de filtros por período.
- **[Visão incompleta de vendas]** → usar os registros de venda e item_pedido já persistidos, sem inventar dados derivados.
- **[Acesso indevido]** → verificar autorização no backend em cada endpoint de resumo.
- **[Dados inconsistentes]** → manter a agregação baseada nas tabelas já aprovadas, sem criar novas tabelas de cache.

## Migration Plan

1. Validar e publicar os endpoints de leitura agregada no Xano do desenvolvimento.
2. Cobrir autorização e respostas com o perfil gestor e colaborador.
3. Integrar a tela do dashboard no Reflex com cards e alertas.
4. Validar a compilação do frontend e o comportamento de acesso por perfil.
5. Caso seja necessário reverter, remover somente a nova tela e endpoints de leitura sem impactar a base transacional existente.
