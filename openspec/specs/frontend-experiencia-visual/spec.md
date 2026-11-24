# frontend-experiencia-visual Specification

## Purpose

Definir uma experiência visual consistente e responsiva para o frontend do FarmaGestão, alinhada ao protótipo e adequada aos fluxos de gestor e colaborador.

## Requirements

### Requirement: Interface segue a identidade visual do protótipo
O frontend SHALL apresentar fundo em tons claros de verde, superfícies em cartões, bordas e sombras consistentes, tipografia legível, botões com hierarquia visual e estados de sucesso, alerta e erro distinguíveis.

#### Scenario: Tela de login apresenta identidade visual
- **WHEN** um usuário acessa a tela de login
- **THEN** o sistema exibe a marca FarmaGestão em painel destacado, seleção visual de perfil e formulário de acesso com os estilos definidos no protótipo

#### Scenario: Telas autenticadas compartilham layout
- **WHEN** um gestor ou colaborador acessa uma tela protegida
- **THEN** o sistema apresenta cabeçalho, navegação, conteúdo em cartões e controles com o mesmo sistema visual

### Requirement: Painel e módulos exibem informações em componentes apropriados
O frontend SHALL organizar indicadores em cards, registros em tabelas responsivas, categorias de conteúdo em abas, estados vazios em mensagens orientativas e operações destrutivas em modais de confirmação.

#### Scenario: Gestor visualiza o painel
- **WHEN** um gestor acessa o painel
- **THEN** o sistema exibe indicadores resumidos, alertas de estoque, produtos mais vendidos e vendas recentes com hierarquia visual clara

#### Scenario: Usuário consulta uma listagem
- **WHEN** um usuário autorizado acessa produtos, estoque, clientes, equipe, fornecedores ou vendas
- **THEN** o sistema exibe os registros em uma tabela ou lista responsiva com ações compatíveis com o perfil

#### Scenario: Usuário executa operação destrutiva
- **WHEN** um usuário inicia remoção ou inativação
- **THEN** o sistema abre confirmação visual antes de enviar a operação e informa o resultado após a resposta

### Requirement: Experiência permanece adaptável e orientada por perfil
O frontend SHALL manter informações e ações utilizáveis em viewport estreito e não SHALL expor controles de módulos não autorizados ao perfil autenticado.

#### Scenario: Colaborador navega no sistema
- **WHEN** um colaborador autenticado acessa o frontend
- **THEN** a navegação exibe somente atendimento, vendas, clientes, estoque e minha conta, sem controles de gestão

#### Scenario: Tela é visualizada em dispositivo estreito
- **WHEN** uma tela é aberta em viewport móvel ou estreito
- **THEN** o conteúdo se reorganiza sem corte horizontal indevido e os formulários, tabelas e ações principais permanecem acessíveis

#### Scenario: Erro de backend é retornado
- **WHEN** uma operação falha por permissão, validação ou indisponibilidade
- **THEN** o frontend apresenta uma mensagem visual no contexto da tela sem ocultar silenciosamente o erro nem alterar o contrato HTTP existente

### Requirement: Componentes visuais reproduzem a composição do protótipo
O frontend SHALL aproximar a composição visual do protótipo, incluindo decoração de fundo na autenticação, cabeçalho compacto, navegação em abas, cartões com hierarquia de conteúdo, tabelas/listas com cabeçalhos, badges semânticos e modais centralizados.

#### Scenario: Login exibe composição decorativa
- **WHEN** a tela de login é aberta
- **THEN** o painel de acesso aparece sobre o fundo verde com elementos decorativos suaves, mantendo contraste e legibilidade

#### Scenario: Módulo exibe navegação e conteúdo
- **WHEN** um usuário acessa um módulo autenticado
- **THEN** o cabeçalho e as abas de navegação ficam visualmente separados do conteúdo, que é organizado em cartões e seções com títulos e descrições

#### Scenario: Registro exibe estado semântico
- **WHEN** uma listagem apresenta canal, situação, alerta ou ação destrutiva
- **THEN** o frontend usa badge, cor e botão coerentes com o significado, sem depender apenas de texto ou cor isolada
