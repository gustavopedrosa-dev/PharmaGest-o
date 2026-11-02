## MODIFIED Requirements

### Requirement: Gestor visualiza painel executivo
O sistema SHALL permitir que um gestor autenticado consulte um resumo do dia local com vendas concluídas, faturamento, quantidade de funcionários ativos, produtos em alerta de estoque e quantidade vendida por medicamento.

#### Scenario: Gestor acessa o painel
- **WHEN** um gestor autenticado abre o painel
- **THEN** o sistema retorna os indicadores referentes ao intervalo entre o início do dia local e o início do próximo dia

#### Scenario: Colaborador tenta acessar o painel
- **WHEN** um colaborador autenticado tenta acessar a rota ou o endpoint do painel
- **THEN** o sistema redireciona a rota para a área do colaborador ou rejeita o endpoint com HTTP 403, sem retornar indicadores

### Requirement: Quantidade vendida por medicamento é calculada com base no histórico
O sistema SHALL calcular a quantidade por medicamento somente a partir dos itens de vendas concluídas no período solicitado e apresentar o ranking em ordem decrescente de quantidade.

#### Scenario: Vendas confirmadas são agregadas
- **WHEN** há itens vinculados a vendas concluídas dentro do período solicitado
- **THEN** o sistema soma a quantidade por medicamento e ordena o resultado da maior para a menor quantidade

#### Scenario: Vendas não confirmadas não entram no relatório
- **WHEN** há itens de pedido pendente, venda estornada ou venda fora do período solicitado
- **THEN** esses itens não alteram o ranking nem os totais do painel