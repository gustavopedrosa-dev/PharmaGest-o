## MODIFIED Requirements

### Requirement: Endereços pertencem a clientes

O sistema SHALL permitir que um colaborador autenticado cadastre, consulte e edite múltiplos endereços vinculados a um cliente existente, e SHALL impedir endereços sem cliente associado.

#### Scenario: Colaborador cadastra endereço

- **WHEN** um colaborador envia um endereço válido para um cliente existente
- **THEN** o sistema cria o endereço vinculado ao cliente informado e retorna seus dados

#### Scenario: Colaborador consulta e edita endereços do cliente

- **WHEN** um colaborador abre a edição de um cliente com um ou mais endereços
- **THEN** o sistema apresenta os endereços vinculados ao cliente com seus campos preenchidos
- **AND** ao salvar alterações de um endereço, atualiza o mesmo registro sem criar uma cópia

#### Scenario: Colaborador adiciona endereço adicional

- **WHEN** um colaborador adiciona um endereço válido a um cliente que já possui endereços
- **THEN** o sistema cria um novo endereço para esse cliente e preserva os endereços existentes

#### Scenario: Endereço pertence a outro cliente

- **WHEN** um colaborador tenta editar um endereço que não pertence ao cliente informado
- **THEN** o sistema rejeita a operação e não altera nenhum endereço

#### Scenario: Gestor tenta editar endereço

- **WHEN** um gestor tenta editar um endereço de cliente
- **THEN** o sistema rejeita a operação com erro de permissão e mantém os dados inalterados

#### Scenario: Cliente inexistente

- **WHEN** um colaborador tenta cadastrar, consultar ou editar endereços de um cliente inexistente
- **THEN** o sistema rejeita a operação informando que o cliente não foi encontrado

#### Scenario: Gestor consulta endereços

- **WHEN** um gestor autenticado consulta os dados de um cliente
- **THEN** o sistema permite visualizar os endereços vinculados a esse cliente
