## 1. Preparação e modelo de dados

- [x] 1.1 Auditar os schemas atuais de `pedido`, `item_pedido`, `venda`, `pagamento`, `receita`, `item_receita` e `cliente`, registrando campos e índices existentes sem incluir dados sensíveis no snapshot.
- [x] 1.2 Adicionar de forma aditiva os campos de canal do pedido, número da receita e situação ativa do cliente, com defaults compatíveis e índices necessários; validar que nenhuma tabela fora do escopo é criada.
- [x] 1.3 Definir e validar os estados permitidos de pedido e venda, formas de pagamento aceitas e regras de quantidade, preço e vínculos obrigatórios.

## 2. APIs e regras de pedidos

- [x] 2.1 Criar funções backend para validar sessão, atendente, cliente ativo, produtos ativos, itens únicos e quantidades positivas; verificar que payloads inválidos não geram registros parciais.
- [x] 2.2 Criar endpoint protegido para colaborador criar pedido pendente, derivando `id_funcionario` da sessão e capturando o preço unitário; validar HTTP 200 para entrada válida e HTTP 403 para gestor.
- [x] 2.3 Criar endpoint protegido para consultar pedidos e itens conforme o perfil, filtrando colaborador pelos próprios atendimentos e gestor pelo histórico autorizado; validar HTTP 401 sem sessão.
- [x] 2.4 Implementar validação de cliente balcão, cliente ativo e produto controlado no pedido; verificar que cliente inativo não pode ser usado em nova venda.

## 3. Confirmação, pagamento e estoque

- [x] 3.1 Criar função transacional de confirmação que revalide estado, itens, produtos ativos e estoque antes de alterar qualquer registro; verificar falha sem alterações.
- [x] 3.2 Integrar a baixa transacional de todos os produtos à confirmação e impedir estoque negativo, incluindo concorrência sobre o último saldo; validar saldo e rollback.
- [x] 3.3 Criar endpoint de confirmação para colaborador com forma de pagamento em dinheiro, cartão ou Pix, calculando total no backend e criando venda/pagamento em uma operação; verificar HTTP 200 e persistência consistente.
- [x] 3.4 Rejeitar quantidade insuficiente, pagamento inválido, confirmação repetida e pedido cancelado; verificar códigos 4xx e ausência de venda, pagamento ou baixa parcial.
- [x] 3.5 Impedir edição e exclusão de vendas, itens, pagamentos e receitas após confirmação; verificar que endpoints administrativos inexistentes ou protegidos não alteram histórico.

## 4. Medicamentos controlados

- [x] 4.1 Exigir cliente ativo e número de receita para pedidos que contenham produto controlado; validar que produto comum continua aceitando cliente balcão.
- [x] 4.2 Criar receita e itens de receita para cada controlado confirmado, vinculando cliente, produto e quantidade vendida na mesma transação; verificar rollback quando o vínculo falhar.
- [x] 4.3 Cobrir contrato HTTP de venda controlada com e sem cliente, com e sem receita e com múltiplos controlados; confirmar estoque e histórico em cada cenário.

## 5. Integração Reflex

- [x] 5.1 Adicionar dataclasses e métodos server-side ao cliente Xano para pedidos, confirmação e consultas, preservando token privado e tratamento explícito de 401/403/4xx/5xx/timeouts; cobrir transporte com testes mockados.
- [x] 5.2 Criar tela de atendimento para colaborador com inclusão de itens, quantidades, canal, cliente opcional, receita quando necessária e forma de pagamento; verificar estados de validação e sucesso.
- [x] 5.3 Criar tela de consulta de vendas para colaborador e gestor com filtros autorizados, itens, total, canal, atendente e pagamento; verificar que histórico não oferece edição ou exclusão.
- [x] 5.4 Integrar navegação e proteção de rotas por perfil, exibindo ações de atendimento somente ao colaborador e consulta administrativa ao gestor; verificar redirecionamento sem sessão.

## 6. Verificação integrada

- [x] 6.1 Executar contrato HTTP autenticado para pedidos, confirmação, pagamentos, permissões, estoque insuficiente, concorrência e imutabilidade do histórico.
- [x] 6.2 Executar fluxo ponta a ponta no Reflex com contas temporárias de gestor e colaborador, incluindo venda comum, venda controlada, consulta, tentativa indevida e logout; inativar as contas ao final.
- [x] 6.3 Executar compilação Reflex, testes unitários do cliente, validação OpenSpec estrita, `git diff --check` e `xano workspace push --dry-run`; confirmar ausência de credenciais e tabelas fora do escopo.
