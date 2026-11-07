## Context

O frontend atual está concentrado em `connectdrogs/connectdrogs.py`, já possui páginas e eventos integrados ao cliente Xano, e mantém o token no estado server-side. O protótipo HTML define uma linguagem visual própria, mas seus dados fictícios e regras de negócio não devem ser copiados para a aplicação.

## Goals / Non-Goals

**Goals:**

- Criar um sistema visual reutilizável para login, navegação, cards, tabelas, formulários, abas, badges, alertas e modais.
- Reorganizar as páginas existentes para aproximá-las do protótipo em desktop e viewport estreito.
- Preservar os eventos, estados, chamadas Xano, mensagens de erro e proteção por perfil já implementados.
- Validar compilação, testes automatizados e fluxos visuais essenciais.

**Non-Goals:**

- Alterar endpoints, XanoScript, tabelas ou regras de autorização.
- Introduzir outro framework de frontend ou substituir Reflex.
- Recriar dados fictícios do protótipo como dados da aplicação.
- Adicionar funcionalidades de domínio que não existem nas specs atuais.

## Decisions

### Sistema visual compartilhado no Reflex

Criar funções/componentes de apresentação e constantes de estilo reutilizáveis dentro do frontend, em vez de duplicar propriedades em cada página. Isso mantém as telas consistentes e permite ajustar a identidade visual em um único lugar.

Alternativa considerada: criar uma folha HTML/JavaScript paralela ao Reflex. Foi descartada porque duplicaria o estado e quebraria a integração server-side existente.

### Layout autenticado com navegação orientada por perfil

Manter um layout protegido único, mas separar visualmente cabeçalho, navegação e área de conteúdo. A lista de links continuará derivada de `is_gestor`, preservando a autorização de backend e evitando que a reformulação seja usada como mecanismo de segurança.

Alternativa considerada: criar layouts independentes para cada perfil. Foi descartada por duplicar estrutura e aumentar o risco de divergência visual.

### Responsividade por composição

Usar largura máxima, espaçamento, grids que colapsam e tabelas/listas com rolagem controlada quando necessário. Formulários e ações serão organizados para que o fluxo principal continue acessível em telas estreitas.

Alternativa considerada: esconder colunas ou ações automaticamente. Será evitado quando isso remover informação essencial; a adaptação deve preservar conteúdo e permissões.

### Feedback visual sem alteração do contrato de erros

Centralizar a apresentação de mensagens já produzidas pelos eventos do estado, diferenciando informação, sucesso, validação, permissão e indisponibilidade por estilo. Nenhuma falha será convertida em sucesso ou descartada.

### Segunda rodada de fidelidade ao protótipo

Adicionar uma camada visual dedicada à composição do protótipo: blobs decorativos somente na autenticação, superfícies translúcidas onde apropriado, cabeçalho compacto e uma barra de navegação com aparência de abas. Nas listagens, priorizar cartões de seção, cabeçalhos de tabela e badges semânticos antes de ajustar dimensões por tela.

Os dados continuam vindo do estado Reflex e as ações permanecem nos handlers existentes. A aproximação será feita com componentes de apresentação e estilos compartilhados, sem copiar o JavaScript ou os dados fictícios do arquivo HTML.

Alternativa considerada: reconstruir o protótipo HTML dentro de um componente web separado. Foi descartada porque criaria uma segunda árvore de renderização e dificultaria a preservação da sessão server-side.

## Risks / Trade-offs

- [Risco] A grande quantidade de páginas concentradas em um arquivo pode tornar a refatoração extensa. -> Mitigação: aplicar componentes compartilhados por etapas e validar a compilação após cada grupo de telas.
- [Risco] Uma mudança visual pode alterar acidentalmente bindings ou eventos Reflex. -> Mitigação: preservar handlers e nomes de estado, executar a suíte existente e testar os fluxos críticos no navegador.
- [Risco] Tabelas extensas podem não caber em telas estreitas. -> Mitigação: usar composição responsiva e rolagem horizontal localizada apenas na área da tabela.
- [Risco] O OneDrive pode bloquear artefatos gerados durante execução do Reflex. -> Mitigação: validar primeiro com `reflex compile --dry` e registrar qualquer limitação de execução sem alterar regras do produto.
