## MODIFIED Requirements

### Requirement: Gestor administra produtos e categorias
O sistema SHALL permitir que somente o gestor crie, edite e inative produtos e categorias, mantendo os vínculos obrigatórios com categoria e fornecedor e sem permitir que o colaborador execute essas operações.

#### Scenario: Gestor cadastra produto válido
- **WHEN** um gestor informa nome, categoria, preço, quantidade em estoque, estoque mínimo e indicação de controlado válidos, selecionando um fornecedor cadastrado no catálogo
- **THEN** o sistema valida o fornecedor no backend, cria o produto ativo com os dados informados e o disponibiliza para consulta

#### Scenario: Gestor edita produto
- **WHEN** um gestor altera os dados de um produto existente
- **THEN** o sistema atualiza somente o produto informado e preserva os vínculos e os valores já registrados em vendas

#### Scenario: Gestor inativa produto
- **WHEN** um gestor confirma a inativação de um produto
- **THEN** o produto deixa de ser oferecido para novas vendas, mas permanece disponível para histórico e consulta autorizada

#### Scenario: Colaborador tenta administrar produto ou categoria
- **WHEN** um colaborador tenta criar, editar ou inativar produto ou categoria
- **THEN** a API recusa a operação com HTTP 403 e não altera dados