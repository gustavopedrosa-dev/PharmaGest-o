## ADDED Requirements

### Requirement: Resumo do painel exige perfil gestor
O endpoint de resumo do painel SHALL exigir sessão válida e perfil `gestor`, aplicando a autorização no backend independentemente da navegação do Reflex.

#### Scenario: Consulta sem sessão válida
- **WHEN** uma requisição ao resumo do painel não apresenta token válido
- **THEN** a API responde HTTP 401 e não retorna indicadores

#### Scenario: Colaborador consulta o resumo
- **WHEN** uma requisição autenticada com perfil `colaborador` consulta o resumo do painel
- **THEN** a API responde HTTP 403 e não retorna indicadores