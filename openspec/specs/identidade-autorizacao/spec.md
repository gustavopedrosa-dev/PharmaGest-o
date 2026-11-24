# identidade-autorizacao Specification

## Purpose

Estabelece autenticação única e autorização por perfil para Gestor e Colaborador, vinculando cada conta ao funcionário e protegendo os fluxos do FarmaGestão.

## Requirements

### Requirement: Login identifica usuário ativo sem revelar credenciais
O sistema SHALL autenticar pela tabela `usuario`, aceitar somente os perfis `gestor` e `colaborador`, recusar contas inativas e apresentar a mensagem genérica "usuário ou senha inválidos" quando o login ou a senha não forem válidos.

#### Scenario: Login válido de usuário ativo
- **WHEN** um usuário ativo informa login e senha válidos
- **THEN** o sistema autentica a conta e retorna uma sessão associada ao funcionário e ao perfil correspondentes

#### Scenario: Credencial inválida ou conta inativa
- **WHEN** o login não existe, a senha não confere ou a conta está inativa
- **THEN** o sistema recusa a autenticação com a mensagem "usuário ou senha inválidos" e não emite token

### Requirement: Login direciona o usuário conforme seu perfil

Após autenticação bem-sucedida, o Reflex SHALL direcionar gestores ao painel (`/dashboard`) e colaboradores à página Minhas vendas (`/vendas`), sem apresentar mensagem de falta de permissão no fluxo normal de entrada.

#### Scenario: Gestor entra após login válido

- **WHEN** um gestor ativo informa credenciais válidas
- **THEN** o sistema o direciona ao painel do gestor

#### Scenario: Colaborador entra após login válido

- **WHEN** um colaborador ativo informa credenciais válidas
- **THEN** o sistema o direciona à página Minhas vendas com a sessão autenticada
- **AND** não apresenta mensagem de falta de permissão

### Requirement: Primeiro gestor é provisionado uma única vez fora da API pública
O sistema SHALL permitir que um integrante autorizado do grupo execute manualmente no Xano uma função de bootstrap que receba os dados do gestor no momento da execução, crie funcionário com cargo `Gestor` e usuário ativo com perfil `gestor`, e não exponha credenciais em código versionado, endpoint público ou resposta persistida.

#### Scenario: Bootstrap sem gestor cadastrado
- **WHEN** a função é executada e não existe nenhum usuário com perfil `gestor`
- **THEN** ela cria o funcionário e a conta vinculada, usando a senha fornecida somente para gerar a credencial protegida

#### Scenario: Bootstrap executado após existir gestor
- **WHEN** a função é executada e já existe uma conta com perfil `gestor`, ativa ou inativa
- **THEN** ela não cria outro gestor e informa que o bootstrap já foi realizado

#### Scenario: Tentativa de bootstrap por endpoint público
- **WHEN** um cliente externo tenta criar ou promover um gestor por uma API pública
- **THEN** nenhuma rota pública permite essa operação

### Requirement: Sessão tem validade limitada e representa a identidade atual
O sistema SHALL emitir token com validade de oito horas para login válido, permitir consultar a sessão atual e invalidar localmente a sessão quando o usuário sair ou o token for recusado/expirar.

#### Scenario: Consulta de sessão válida
- **WHEN** o cliente servidor apresenta um token válido
- **THEN** a API retorna a identidade atual, o funcionário e o perfil sem expor a senha ou seu hash

#### Scenario: Token ausente, inválido ou expirado
- **WHEN** uma rota protegida recebe token ausente, inválido ou expirado
- **THEN** a API responde HTTP 401 e o Reflex limpa a sessão e encaminha o usuário ao login com a mensagem "Sessão expirada. Entre novamente."

#### Scenario: Logout
- **WHEN** o usuário encerra a sessão
- **THEN** o Reflex remove o token da sessão server-side e exige novo login para páginas protegidas

### Requirement: Autorização é aplicada no backend a cada chamada
O sistema SHALL determinar as permissões a partir do usuário autenticado e consultar no banco seu perfil e estado ativo a cada chamada protegida; parâmetros ou estado fornecidos pelo frontend não podem conceder ou alterar perfil.

#### Scenario: Gestor passa pela rota temporária de teste
- **WHEN** um gestor ativo chama a rota temporária de verificação no ambiente Xano de desenvolvimento
- **THEN** a rota usa a mesma função de autorização das rotas reais e responde HTTP 200

#### Scenario: Colaborador é recusado pela rota temporária de teste
- **WHEN** um colaborador ativo chama a rota temporária de verificação no ambiente Xano de desenvolvimento
- **THEN** a rota usa a mesma função de autorização das rotas reais e responde HTTP 403 sem executar a operação

#### Scenario: Rota temporária é chamada sem token
- **WHEN** uma chamada sem token válido acessa a rota temporária de verificação
- **THEN** a API responde HTTP 401

#### Scenario: Rota temporária é removida antes da integração
- **WHEN** a Change está pronta para ser integrada
- **THEN** a rota temporária de verificação já foi removida do Xano e não consta no export final

#### Scenario: Conta é inativada durante uma sessão
- **WHEN** uma conta autenticada é inativada no banco e depois chama uma rota protegida
- **THEN** a API responde HTTP 401 mesmo que o token ainda não tenha expirado, e o Reflex encerra a sessão

### Requirement: Gestor e colaborador gerenciam somente as próprias credenciais
O sistema SHALL permitir que somente um colaborador ativo altere o próprio login e senha, exigir a senha atual para a troca de senha, manter a sessão atual ativa após a troca e preservar a associação com o funcionário e o perfil. O sistema SHALL recusar logins que já estejam em uso e SHALL rejeitar gestores nessa capacidade.

#### Scenario: Gestor altera o próprio login
- **WHEN** um gestor tenta salvar um novo login na área Minha conta
- **THEN** a interface não oferece essa operação e a API responde erro de permissão sem alterar a conta

#### Scenario: Gestor troca a própria senha
- **WHEN** um gestor tenta trocar a senha na área Minha conta
- **THEN** a interface não oferece essa operação e a API responde erro de permissão sem alterar a conta

#### Scenario: Gestor não altera credenciais pela área Minha conta
- **WHEN** um gestor tenta acessar a área Minha conta ou chamar diretamente suas operações
- **THEN** o Reflex não oferece a área e a API responde erro de permissão sem alterar a conta

#### Scenario: Colaborador altera o próprio login
- **WHEN** um colaborador ativo salva um login disponível na área Minha conta
- **THEN** somente o login da sua própria conta é atualizado e o perfil permanece `colaborador`

#### Scenario: Colaborador troca a própria senha
- **WHEN** um colaborador ativo informa a senha atual correta e uma nova senha válida
- **THEN** somente a senha da sua própria conta é atualizada com hash, o perfil permanece `colaborador` e a sessão continua ativa

#### Scenario: Senha atual incorreta
- **WHEN** um colaborador informa uma senha atual incorreta ao tentar alterá-la
- **THEN** a API recusa a alteração, mantém a senha existente e a sessão atual

#### Scenario: Login escolhido já está em uso
- **WHEN** um colaborador tenta salvar um login utilizado por outra conta
- **THEN** a API recusa a alteração e o Reflex apresenta a mensagem de validação

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

### Requirement: Autenticação Quick Start deixa de ser oferecida
O sistema SHALL remover as tabelas Quick Start `user` e `event_log` e deixar de expor os endpoints, addons e funções que dependem delas, incluindo cadastro público, autenticação genérica, recuperação de senha, e-mail de boas-vindas e logs vinculados à identidade antiga.

#### Scenario: Cliente tenta usar cadastro público legado
- **WHEN** um cliente solicita cadastro pelo endpoint Quick Start
- **THEN** o endpoint não está disponível e nenhuma conta é criada

#### Scenario: Aplicação usa a identidade do domínio
- **WHEN** uma operação autenticada do FarmaGestão é executada
- **THEN** a identidade e autorização usam `usuario` vinculada a `funcionario`, sem consultar a tabela `user`

### Requirement: Resumo do painel exige perfil gestor
O endpoint de resumo do painel SHALL exigir sessão válida e perfil `gestor`, aplicando a autorização no backend independentemente da navegação do Reflex.

#### Scenario: Consulta sem sessão válida
- **WHEN** uma requisição ao resumo do painel não apresenta token válido
- **THEN** a API responde HTTP 401 e não retorna indicadores

#### Scenario: Colaborador consulta o resumo
- **WHEN** uma requisição autenticada com perfil `colaborador` consulta o resumo do painel
- **THEN** a API responde HTTP 403 e não retorna indicadores
