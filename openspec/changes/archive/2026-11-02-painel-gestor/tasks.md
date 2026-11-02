## 1. Preparação e dados do painel

- [x] 1.1 Revisar as tabelas e endpoints existentes de vendas, produtos e funcionários para identificar os dados mínimos do dashboard sem criar campos novos.
- [x] 1.2 Definir os indicadores do painel e os filtros de período compatíveis com o domínio do FarmaGestão.
- [x] 1.3 Validar que o dashboard depende de dados já existentes e não amplia o escopo do banco.

## 2. APIs de leitura do painel

- [x] 2.1 Criar endpoint de resumo do gestor para vendas do dia e totais gerais, com autorização por perfil.
- [x] 2.2 Criar endpoint para listar produtos abaixo do estoque mínimo e suas quantidades pendentes.
- [x] 2.3 Criar endpoint para listar a quantidade vendida por medicamento no período selecionado.
- [x] 2.4 Criar endpoint para contar funcionários ativos e validar que o colaborador não recebe esses dados.
- [x] 2.5 Verificar respostas 401 sem sessão e 403 para colaborador em cada endpoint do painel.

## 3. Integração Reflex

- [x] 3.1 Criar tela do painel exclusivo para gestor, com cards dos principais indicadores.
- [x] 3.2 Exibir produtos em alerta de reposição e ranking de itens vendidos.
- [x] 3.3 Redirecionar tentativas de acesso de colaborador para a área apropriada.
- [x] 3.4 Conectar a tela ao estado server-side e manter a lógica de autenticação centralizada.

## 4. Verificação integrada

- [x] 4.1 Executar fluxo de login de gestor e validar que o painel abre corretamente.
- [x] 4.2 Executar login de colaborador e validar bloqueio de acesso.
- [x] 4.3 Compilar o Reflex e confirmar que a navegação do dashboard não quebra o restante do sistema.
- [x] 4.4 Validar a estrutura OpenSpec e confirmar que a change está pronta para revisão e arquivamento.
