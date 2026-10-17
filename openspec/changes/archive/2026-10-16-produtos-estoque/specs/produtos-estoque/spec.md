## Purpose

Define o cadastro de produtos e categorias e mantém o estoque disponível para consulta e para as validações das vendas do FarmaGestão, com permissões distintas para gestor e colaborador.

## ADDED Requirements

### Requirement: Gestor administra produtos e categorias
O sistema SHALL permitir que somente o gestor crie, edite e inative produtos e categorias, mantendo os vínculos obrigatórios com categoria e fornecedor e sem permitir que o colaborador execute essas operações.

#### Scenario: Gestor cadastra produto válido
- **WHEN** um gestor informa nome, categoria, fornecedor, preço, quantidade em estoque, estoque mínimo e indicação de controlado válidos
- **THEN** o sistema cria o produto ativo com esses dados e o disponibiliza para consulta

#### Scenario: Gestor edita produto
- **WHEN** um gestor altera os dados de um produto existente
- **THEN** o sistema atualiza somente o produto informado e preserva os vínculos e os valores já registrados em vendas

#### Scenario: Gestor inativa produto
- **WHEN** um gestor confirma a inativação de um produto
- **THEN** o produto deixa de ser oferecido para novas vendas, mas permanece disponível para histórico e consulta autorizada

#### Scenario: Colaborador tenta administrar produto ou categoria
- **WHEN** um colaborador tenta criar, editar ou inativar produto ou categoria
- **THEN** a API recusa a operação com HTTP 403 e não altera dados

### Requirement: Produto mantém dados de estoque e reposição
O sistema SHALL armazenar no próprio produto a quantidade em estoque e o estoque mínimo, aceitar somente valores não negativos e sinalizar quando a quantidade estiver abaixo do mínimo.

#### Scenario: Produto é criado com estoque válido
- **WHEN** o gestor informa quantidade em estoque e estoque mínimo maiores ou iguais a zero
- **THEN** o produto é salvo com esses valores e sem criar lote ou movimentação de estoque

#### Scenario: Estoque inválido é recusado
- **WHEN** o gestor informa quantidade em estoque ou estoque mínimo menor que zero
- **THEN** a API recusa a operação com erro de validação e não salva o produto

#### Scenario: Produto abaixo do mínimo é sinalizado
- **WHEN** a quantidade em estoque de um produto fica menor que seu estoque mínimo
- **THEN** a consulta de produtos ou estoque identifica o produto como "repor"

### Requirement: Gestor e colaborador consultam estoque autorizado
O sistema SHALL permitir que gestor e colaborador consultem produtos ativos, preço, categoria, fornecedor, indicação de controlado, quantidade em estoque e situação de reposição, sem expor operações de administração ao colaborador.

#### Scenario: Gestor consulta estoque
- **WHEN** um gestor acessa a consulta de estoque
- **THEN** o sistema retorna os produtos autorizados e identifica os itens abaixo do estoque mínimo

#### Scenario: Colaborador consulta estoque
- **WHEN** um colaborador acessa a consulta de estoque
- **THEN** o sistema retorna os produtos necessários ao atendimento e não apresenta ações de cadastro, edição ou inativação

#### Scenario: Usuário sem sessão consulta estoque
- **WHEN** uma chamada de consulta de estoque é feita sem token válido
- **THEN** a API responde HTTP 401 e não retorna dados

### Requirement: Estoque não pode ser reduzido abaixo de zero por venda
O sistema SHALL impedir que uma operação de venda reduza o estoque abaixo de zero ou aceite quantidade superior à disponível, mantendo a decisão no backend.

#### Scenario: Venda dentro do estoque disponível
- **WHEN** uma venda informa quantidade positiva menor ou igual ao estoque disponível
- **THEN** a operação é aceita e o estoque do produto é reduzido pela quantidade vendida

#### Scenario: Venda acima do estoque disponível
- **WHEN** uma venda informa quantidade maior que o estoque disponível
- **THEN** a API recusa a venda com erro de regra e mantém o estoque inalterado

#### Scenario: Venda de produto sem estoque
- **WHEN** uma venda tenta incluir produto com quantidade em estoque igual a zero
- **THEN** a API recusa a venda e mantém o estoque em zero
