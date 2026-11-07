## 1. Sistema visual e layout compartilhado

- [x] 1.1 Definir tokens de cor, tipografia, espaçamento, bordas, sombras e estados visuais reutilizáveis no Reflex e verificar que `reflex compile --dry` passa
- [x] 1.2 Reestruturar o layout autenticado, cabeçalho e navegação por perfil conforme o protótipo e verificar que gestor e colaborador veem somente seus links
- [x] 1.3 Criar componentes compartilhados para cards, tabelas responsivas, abas, badges, alertas, estados vazios e modais, verificando uso consistente em pelo menos duas telas

## 2. Login e painel

- [x] 2.1 Reformular a tela de login com seleção visual de perfil, painel destacado e mensagens de erro sem expor senha, verificando login válido e inválido no navegador
- [x] 2.2 Reformular o painel do gestor com cards de indicadores, alertas de estoque, mais vendidos e vendas recentes, verificando carregamento e estado vazio com dados reais do Xano

## 3. Módulos operacionais e administrativos

- [x] 3.1 Adaptar produtos e estoque ao padrão visual do protótipo, preservando seleção de fornecedor, edição, alertas e permissões, verificando o fluxo de cadastro e consulta
- [x] 3.2 Adaptar clientes, equipe e fornecedores com tabelas, formulários e modais responsivos, verificando confirmação/cancelamento e mensagens de erro
- [x] 3.3 Adaptar atendimento, vendas e histórico com abas, seleção de produtos, resumo do pedido, badges de canal e tratamento visual de erros, verificando o fluxo de venda
- [x] 3.4 Adaptar Minha conta e estados de sessão/indisponibilidade, verificando expiração de sessão, erro 403 e erro 5xx sem expor o token

## 4. Validação integrada

- [x] 4.1 Verificar comportamento responsivo em viewport desktop e estreito para login, painel e módulos principais, sem corte indevido de ações
- [x] 4.2 Executar `pytest -q` com `PYTHONPATH` configurado, `reflex compile --dry` e validação OpenSpec, confirmando que os fluxos existentes permanecem íntegros

## 5. Fidelidade visual adicional ao protótipo

- [x] 5.1 Reproduzir a composição do login com fundo verde em gradiente, blobs decorativos, painel translúcido e cards de perfil, verificando a aparência em desktop e viewport estreito
- [x] 5.2 Reestruturar o cabeçalho autenticado para se aproximar da barra compacta do protótipo, com abas ativas, agrupamento por perfil e identificação do usuário, verificando navegação de gestor e colaborador
- [x] 5.3 Reorganizar listagens e histórico em cartões com cabeçalhos, colunas legíveis e badges semânticos para canal, situação e alertas, verificando fornecedores, produtos e vendas
- [x] 5.4 Padronizar modais, botões secundários/destrutivos, estados vazios e mensagens de feedback conforme as cores e espaçamentos do protótipo, verificando confirmação e cancelamento
- [x] 5.5 Validar visualmente a segunda rodada no navegador e executar `pytest -q`, `reflex compile --dry` e `openspec validate --strict`
