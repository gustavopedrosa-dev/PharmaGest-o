## ADDED Requirements

### Requirement: Login direciona o usuário conforme seu perfil

Após autenticação bem-sucedida, o Reflex SHALL direcionar gestores ao painel (`/dashboard`) e colaboradores à página Minhas vendas (`/vendas`), sem apresentar mensagem de falta de permissão no fluxo normal de entrada.

#### Scenario: Gestor entra após login válido

- **WHEN** um gestor ativo informa credenciais válidas
- **THEN** o sistema o direciona ao painel do gestor

#### Scenario: Colaborador entra após login válido

- **WHEN** um colaborador ativo informa credenciais válidas
- **THEN** o sistema o direciona à página Minhas vendas com a sessão autenticada
- **AND** não apresenta mensagem de falta de permissão
