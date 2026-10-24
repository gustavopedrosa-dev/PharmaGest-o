# clientes Specification

## Purpose

Esta capacidade permite manter clientes identificáveis e ativos para apoiar o histórico de compras e as vendas que exigem cliente cadastrado, sem conceder acesso do cliente ao sistema.

## Requirements

### Requirement: Colaborador administra clientes

O sistema SHALL permitir que um colaborador autenticado consulte, cadastre, edite e inative clientes, respeitando a unicidade do CPF e os campos definidos no modelo de domínio.

#### Scenario: Colaborador cadastra cliente

- **WHEN** um colaborador envia um cadastro válido com nome, CPF e demais dados permitidos
- **THEN** o sistema cria um cliente ativo e retorna seus dados sem credenciais de acesso

#### Scenario: CPF de cliente já cadastrado

- **WHEN** um colaborador tenta cadastrar ou editar um cliente usando um CPF já associado a outro cliente
- **THEN** o sistema rejeita a operação e informa que o CPF já está cadastrado

#### Scenario: Colaborador edita cliente

- **WHEN** um colaborador envia alterações válidas para um cliente existente
- **THEN** o sistema atualiza os dados do cliente sem alterar seu identificador ou histórico de compras

#### Scenario: Colaborador inativa cliente

- **WHEN** um colaborador solicita a inativação de um cliente
- **THEN** o sistema marca o cliente como inativo, mantém seus pedidos e impede seu uso em novos pedidos

### Requirement: Gestor consulta clientes

O sistema SHALL permitir que um gestor autenticado consulte clientes e seus dados cadastrais, sem permitir cadastro, edição ou inativação por essa capacidade.

#### Scenario: Gestor lista clientes

- **WHEN** um gestor autenticado solicita a consulta de clientes
- **THEN** o sistema retorna os clientes conforme os filtros ou a listagem disponíveis, incluindo a situação ativo ou inativo

#### Scenario: Gestor tenta alterar cliente

- **WHEN** um gestor tenta cadastrar, editar ou inativar um cliente
- **THEN** o sistema rejeita a operação com erro de permissão

### Requirement: Endereços pertencem a clientes

O sistema SHALL permitir que um colaborador autenticado cadastre e consulte endereços vinculados a um cliente existente, e SHALL impedir endereços sem cliente associado.

#### Scenario: Colaborador cadastra endereço

- **WHEN** um colaborador envia um endereço válido para um cliente existente
- **THEN** o sistema cria o endereço vinculado ao cliente informado e retorna seus dados

#### Scenario: Cliente inexistente

- **WHEN** um colaborador tenta cadastrar ou consultar endereço de um cliente inexistente
- **THEN** o sistema rejeita a operação informando que o cliente não foi encontrado

#### Scenario: Gestor consulta endereços

- **WHEN** um gestor autenticado consulta os dados de um cliente
- **THEN** o sistema permite visualizar os endereços vinculados a esse cliente

### Requirement: Autorização e sessão são aplicadas no backend

O sistema SHALL exigir uma sessão autenticada e aplicar o perfil de acesso na API para todas as operações de clientes e endereços, independentemente da interface utilizada.

#### Scenario: Usuário não autenticado

- **WHEN** uma requisição de clientes ou endereços não apresenta uma sessão válida
- **THEN** o sistema rejeita a requisição como não autorizada e não altera dados

#### Scenario: Colaborador acessa operação permitida

- **WHEN** um colaborador autenticado executa uma operação de manutenção permitida
- **THEN** o sistema processa a operação conforme as regras da capacidade

#### Scenario: Perfil sem permissão chama a API diretamente

- **WHEN** um gestor chama diretamente um endpoint de manutenção reservado ao colaborador
- **THEN** o sistema rejeita a requisição com erro de permissão e não altera dados