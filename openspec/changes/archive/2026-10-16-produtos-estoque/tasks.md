## 1. Preparação e modelo de dados

- [x] 1.1 Auditar o schema atual de `produto`, `categoria` e `fornecedor` no workspace Xano `v1`, registrar o snapshot sem registros/variáveis de ambiente e verificar que as mudanças propostas são aditivas.
- [x] 1.2 Adicionar ao produto campos para quantidade em estoque, estoque mínimo e estado ativo, com valores padrão compatíveis com registros existentes; validar o schema Xano e a ausência de tabelas de lote/movimentação novas.
- [x] 1.3 Confirmar índices e validações de categoria, fornecedor, preço, estoque e código de barras; executar validação de todos os XanoScripts alterados.

## 2. APIs e regras de produtos

- [x] 2.1 Criar endpoints protegidos para listar e consultar produtos/estoque e verificar HTTP 200 para gestor e colaborador, HTTP 401 sem token e ausência de campos sensíveis não previstos.
- [x] 2.2 Criar endpoints de gestor para cadastrar, editar e inativar produtos e categorias; verificar HTTP 403 para colaborador e confirmar que falhas não alteram dados.
- [x] 2.3 Implementar validação backend para quantidade em estoque e estoque mínimo não negativos, vínculos válidos e preço válido; testar respostas 4xx e persistência inalterada em entradas inválidas.
- [x] 2.4 Implementar a sinalização de reposição quando estoque estiver abaixo do mínimo e excluir produtos inativos das consultas operacionais; verificar os cenários com estoque igual, acima e abaixo do mínimo.
- [x] 2.5 Criar função backend transacional para validar e reduzir estoque em uma futura venda; testar quantidade disponível, quantidade acima do estoque, estoque zero e tentativa concorrente sem permitir saldo negativo.

## 3. Integração Reflex

- [x] 3.1 Adicionar métodos de produtos e estoque ao cliente Xano server-side, preservando o token privado e o tratamento de 401/403/4xx/5xx/timeouts; cobrir respostas com transporte HTTP mockado.
- [x] 3.2 Criar página de gestão de produtos para gestor com listagem, cadastro, edição, inativação e indicação de reposição; verificar compilação e estados de sucesso/erro.
- [x] 3.3 Criar página de consulta de estoque para gestor e colaborador sem ações administrativas para colaborador; verificar navegação, proteção de rota e redirecionamento sem sessão.
- [x] 3.4 Integrar categorias e filtros/indicadores necessários à consulta, sem permitir que valores enviados pelo frontend concedam permissões; verificar visualmente os dois perfis.

## 4. Verificação integrada

- [x] 4.1 Executar contrato HTTP completo para permissões, CRUD, inativação, validações de estoque, sinalização de reposição e função de baixa; confirmar mensagens e códigos esperados.
- [x] 4.2 Executar fluxo ponta a ponta no Reflex para gestor e colaborador, incluindo consulta, administração, logout e tentativa de acesso indevido; verificar que o backend continua sendo a fonte de autorização.
- [x] 4.3 Baixar export final sem registros/variáveis de ambiente, comparar com `xano/`, validar OpenSpec, confirmar ausência de tabelas fora do escopo e verificar que nenhum segredo foi versionado.
