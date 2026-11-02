## Why

O FarmaGestão já entrega autenticação, produtos, clientes, vendas e equipe, mas o gestor ainda não tem uma visão consolidada da operação da farmácia. Sem esse painel, a decisão diária fica dependente de consultas isoladas, e não existe um resumo rápido para estoque crítico, produtividade e volume vendido.

## What Changes

- Criar um painel administrativo para o gestor com indicadores de operação da farmácia.
- Exibir vendas do dia, itens vendidos por medicamento e quantidade de funcionários ativos.
- Listar produtos abaixo do estoque mínimo para reposição prioritária.
- Usar os dados já existentes de vendas, produtos, funcionários e itens de pedido para compor o resumo sem duplicar regras de negócio.
- Restringir o acesso do painel ao perfil gestor e manter a consulta no backend como decisão de autorização.
- Manter fora do escopo a edição de registros diretamente no painel e qualquer relatório financeiro avançado.

## Capabilities

### New Capabilities

- `painel-gestor`: indicadores operacionais do gestor, alertas de estoque e relatório simples de quantidade vendida por medicamento.

### Modified Capabilities

- `identidade-autorizacao`: a API passa a expor o dashboard para o perfil gestor, sem abrir acesso ao colaborador.

## Impact

- **Xano:** endpoints de leitura somente, agregando dados de vendas, produtos e funcionários.
- **Reflex:** tela do painel com cards, alertas e gráficos ou tabelas simples.
- **Autorização:** o gestor acessa; o colaborador recebe 403 ou redirecionamento.
- **Operação:** a visão do gestor se baseia no histórico de vendas e no estoque atual, sem alterar regras nem dados transacionais.
