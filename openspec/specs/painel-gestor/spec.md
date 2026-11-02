# painel-gestor Specification

## Purpose

Entregar ao gestor uma visão consolidada do funcionamento da farmácia, com indicadores de vendas, alertas de estoque e contagem de funcionários ativos, sem abrir dados sensíveis a outros perfis.

## Requirements

### Requirement: Gestor visualiza painel executivo

O sistema SHALL permitir que um gestor autenticado consulte um resumo do dia local com vendas concluídas, faturamento, quantidade de funcionários ativos, produtos em alerta de estoque e quantidade vendida por medicamento.

#### Scenario: Gestor acessa o painel

- **WHEN** um gestor autenticado abre a tela do painel
- **THEN** o sistema retorna os indicadores referentes ao intervalo entre o início do dia local e o início do próximo dia

#### Scenario: Colaborador tenta acessar o painel

- **WHEN** um colaborador autenticado tenta acessar a rota ou endpoint do painel
- **THEN** o sistema redireciona a rota para a área do colaborador ou rejeita o endpoint com HTTP 403, sem retornar indicadores

### Requirement: Produtos abaixo do mínimo aparecem em alerta

O sistema SHALL listar os produtos que estão com quantidade em estoque menor ou igual ao mínimo informado, priorizando reposição para o gestor.

#### Scenario: Produto em risco de estoque

- **WHEN** um produto está abaixo do estoque mínimo
- **THEN** o sistema inclui esse produto na listagem de alertas do painel com o saldo atual e a quantidade mínima

#### Scenario: Produto em nível normal

- **WHEN** um produto não está em risco de estoque
- **THEN** o sistema não inclui esse produto na lista de reposição do painel

### Requirement: Quantidade vendida por medicamento é calculada com base no histórico

O sistema SHALL calcular a quantidade por medicamento somente a partir dos itens de vendas concluídas no período solicitado e apresentar o ranking em ordem decrescente de quantidade.

#### Scenario: Vendas confirmadas são agregadas

- **WHEN** houver vendas confirmadas com produtos específicos
- **THEN** o sistema soma a quantidade por medicamento e ordena o resultado da maior para a menor quantidade

#### Scenario: Vendas não confirmadas não entram no relatório

- **WHEN** houver pedido pendente ou cancelado
- **THEN** esses itens não alteram o ranking nem os totais do painel

### Requirement: Autorização e sessão são aplicadas no backend

O sistema SHALL exigir autenticação válida e aplicar a regra de perfil no backend para todas as consultas do painel, independentemente da interface utilizada.

#### Scenario: Usuário sem sessão consulta painel

- **WHEN** uma requisição ao painel chega sem token válido
- **THEN** o sistema responde como não autorizado e não retorna dados

#### Scenario: Perfil sem permissão consulta painel

- **WHEN** um usuário com perfil colaborador chama a API do painel diretamente
- **THEN** o sistema responde com erro de permissão e não divulga os indicadores do gestor
