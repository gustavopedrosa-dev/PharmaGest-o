## Purpose

Permitir que o gestor mantenha o catálogo de fornecedores e vincule produtos a registros válidos, preservando a integridade dos produtos existentes.

## ADDED Requirements

### Requirement: Gestor administra fornecedores
O sistema SHALL permitir que somente o gestor consulte, cadastre, edite e remova fornecedores, mantendo nome, CNPJ, telefone, e-mail, endereço e prazo de entrega opcional.

#### Scenario: Gestor consulta fornecedores
- **WHEN** um gestor autenticado acessa o catálogo de fornecedores
- **THEN** o sistema retorna os fornecedores cadastrados e os dados disponíveis para seleção em produtos

#### Scenario: Gestor cadastra fornecedor
- **WHEN** um gestor informa nome, CNPJ, e-mail e endereço válidos, podendo informar telefone e prazo de entrega
- **THEN** o sistema cria o fornecedor e preserva o prazo de entrega quando informado

#### Scenario: CNPJ duplicado
- **WHEN** um gestor tenta cadastrar ou atualizar fornecedor com CNPJ já utilizado por outro registro
- **THEN** a API recusa a operação e mantém os registros existentes sem alteração

#### Scenario: Gestor edita fornecedor
- **WHEN** um gestor atualiza os dados de um fornecedor existente com CNPJ válido e disponível
- **THEN** o sistema atualiza somente o fornecedor informado

#### Scenario: Gestor remove fornecedor sem produtos vinculados
- **WHEN** um gestor solicita a remoção de um fornecedor que não está vinculado a nenhum produto
- **THEN** o sistema solicita confirmação e mantém o fornecedor até a confirmação

#### Scenario: Gestor confirma remoção de fornecedor
- **WHEN** um gestor confirma a remoção de um fornecedor sem produtos vinculados
- **THEN** o sistema remove o registro do fornecedor

#### Scenario: Gestor cancela remoção de fornecedor
- **WHEN** um gestor cancela a confirmação de remoção de um fornecedor
- **THEN** o sistema mantém o fornecedor e não chama a API de exclusão

#### Scenario: Gestor tenta remover fornecedor vinculado
- **WHEN** um gestor tenta remover um fornecedor associado a um ou mais produtos
- **THEN** a API recusa a operação com uma mensagem de validação e mantém fornecedor e vínculos intactos

#### Scenario: Colaborador tenta administrar fornecedores
- **WHEN** um colaborador autenticado tenta consultar ou alterar o catálogo de fornecedores
- **THEN** a API responde HTTP 403 e não divulga nem altera os registros

#### Scenario: Requisição sem sessão válida
- **WHEN** uma operação de consulta ou administração de fornecedores é feita sem token válido
- **THEN** a API responde HTTP 401 e não retorna dados nem altera registros