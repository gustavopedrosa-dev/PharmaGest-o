## MODIFIED Requirements

### Requirement: Reflex protege páginas e apresenta o contrato de erros HTTP
O Reflex SHALL manter o token fora do navegador e validar sessão e perfil ao carregar páginas protegidas por meio de chamadas autenticadas ao recurso da página. Quando a página não fizer outra chamada protegida, o Reflex SHALL consultar a sessão. A navegação SHALL continuar carregando dados atualizados a cada entrada, mostrar opções correspondentes ao perfil e tratar respostas HTTP conforme seu significado: 401 encerra a sessão, 403 mantém a sessão e informa falta de permissão, erros 4xx de regra exibem a mensagem do backend, e 5xx ou timeout mostram indisponibilidade sem deslogar.

#### Scenario: Página protegida sem sessão válida
- **WHEN** uma página protegida é carregada sem token no estado server-side
- **THEN** o usuário é encaminhado ao login sem acessar o conteúdo nem fazer uma chamada desnecessária ao Xano

#### Scenario: Gestor navega para uma tela protegida com dados
- **WHEN** um gestor autenticado abre uma tela que carrega dados por uma API protegida
- **THEN** o Reflex carrega os dados e valida a sessão e o perfil pela resposta dessa API, sem uma consulta de sessão separada antes da navegação
- **AND** os dados da tela são atualizados nessa entrada

#### Scenario: Colaborador navega para uma tela protegida com dados
- **WHEN** um colaborador autenticado abre uma tela permitida que carrega dados por uma API protegida
- **THEN** o Reflex carrega os dados e valida a sessão e o perfil pela resposta dessa API, sem uma consulta de sessão separada antes da navegação
- **AND** os dados da tela são atualizados nessa entrada

#### Scenario: Página protegida sem chamada de dados
- **WHEN** uma página protegida precisa da identidade atual e não faz outra chamada protegida ao backend
- **THEN** o Reflex consulta a sessão antes de apresentar o conteúdo

#### Scenario: Token ausente, inválido ou expirado
- **WHEN** uma chamada protegida retorna HTTP 401
- **THEN** o Reflex limpa a sessão e encaminha o usuário ao login com a mensagem "Sessão expirada. Entre novamente."

#### Scenario: Navegação por perfil
- **WHEN** a sessão válida pertence a um gestor ou colaborador
- **THEN** o Reflex apresenta somente as opções de navegação daquele perfil

#### Scenario: Resposta HTTP 403
- **WHEN** uma chamada retorna HTTP 403
- **THEN** o Reflex mantém a sessão e mostra "Você não tem permissão para esta ação"

#### Scenario: Erro de regra de negócio
- **WHEN** uma chamada retorna erro HTTP 4xx com mensagem de validação do backend
- **THEN** o Reflex apresenta essa mensagem no contexto do formulário sem encerrar a sessão

#### Scenario: Indisponibilidade ou timeout
- **WHEN** uma chamada retorna HTTP 5xx ou excede o tempo limite
- **THEN** o Reflex mantém a sessão e mostra "Serviço indisponível, tente novamente"

#### Scenario: Token não é exposto ao navegador
- **WHEN** o Reflex realiza uma chamada autenticada ao Xano
- **THEN** o token é enviado pelo servidor no cabeçalho `Authorization: Bearer` e não fica disponível no estado ou armazenamento do navegador
