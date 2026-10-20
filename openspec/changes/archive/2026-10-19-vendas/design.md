## Context

O Xano já possui as tabelas `pedido`, `item_pedido`, `venda`, `pagamento`, `receita` e `item_receita`, mas os campos de canal, número da receita e situação ativa do cliente ainda não estão completos para o fluxo definido no domínio. A baixa transacional de estoque foi criada na Change `produtos-estoque`, e a autorização existente identifica gestor, colaborador e funcionário da sessão.

## Goals / Non-Goals

**Goals:**

- Entregar um fluxo vertical de atendimento, confirmação e consulta de vendas.
- Garantir atomicidade entre venda, pagamento, receita, pedido e baixa de estoque.
- Preservar o preço praticado e a identidade do atendente no histórico.
- Aplicar as regras de cliente, receita, produto ativo e estoque no backend.
- Manter a interface Reflex coerente com as permissões de gestor e colaborador.

**Non-Goals:**

- Não implementar lotes, validade, pedidos de compra ou movimentação histórica.
- Não implementar parcelas, conciliação ou estorno nesta Change.
- Não criar cadastro médico detalhado; apenas o número da receita é obrigatório para controlados.
- Não permitir edição ou exclusão de registros confirmados.

## Decisions

### Modelo aditivo e compatível

Adicionar somente os campos necessários aos registros existentes: `canal` e, se necessário, `ativo`/`status` no cliente, além de `numero_receita` em receita. Manter os relacionamentos atuais e usar valores padrão ou opcionais compatíveis com dados já existentes. A alternativa de recriar as tabelas foi rejeitada por risco de perda histórica.

### Pedido como agregado da confirmação

O pedido será criado como `pendente`, com itens e preços capturados no momento do atendimento. A confirmação validará o estado, calculará o total a partir dos itens persistidos e aceitará apenas uma transição para `confirmado`. A alternativa de criar venda diretamente a partir do payload do frontend foi rejeitada porque permitiria divergência entre itens, total e estoque.

### Finalização em transação única

A confirmação fará validação de todos os produtos, cliente/receita e pagamento antes de editar qualquer registro; em seguida, dentro de uma transação, reduzirá cada estoque, criará venda/pagamento/receita e confirmará o pedido. A operação reutilizará a mesma lógica de estoque sem executar transações aninhadas que possam deixar etapas parciais.

### Serialização técnica do estoque

Como a atualização por leitura seguida de edição permitiu uma atualização perdida sob confirmações concorrentes no workspace Xano, a confirmação adquirirá locks técnicos únicos por produto dentro da mesma transação. A inserção do lock único serializa disputas pelo produto; a baixa, criação dos registros da venda e liberação dos locks ocorrem antes do commit. A tabela técnica não representa movimentação histórica nem altera o escopo de lotes.

Após a liberação, o registro do lock será reutilizado na próxima confirmação do mesmo produto, evitando que vendas repetidas esgotem a combinação única de produto e estado. A tentativa de adquirir um lock ativo continua protegida pelo índice único.

### Autorização derivada da sessão

O backend obterá `id_funcionario` e perfil do token autenticado. O colaborador poderá criar, confirmar e consultar os próprios pedidos/vendas; o gestor poderá consultar, mas não registrar atendimento. O frontend ocultará ações incompatíveis, porém cada endpoint repetirá a checagem no backend.

### Receita mínima para controlados

Quando houver produto controlado, o pedido exigirá cliente ativo e número de receita. A confirmação criará uma receita vinculada ao cliente e itens de receita com produto e quantidade vendida; dados médicos detalhados permanecerão opcionais e fora do fluxo.

### Cliente balcão

`id_cliente` permanecerá opcional para pedidos sem controlados. O backend rejeitará cliente inativo em novos pedidos e exigirá cliente ativo quando houver controlado. Isso preserva o atendimento de produtos comuns sem inventar um registro de cliente balcão.

## Risks / Trade-offs

- **[Concorrência de estoque]** → validar e reduzir cada produto dentro da mesma transação; cobrir concorrência no contrato HTTP.
- **[Registros legados sem novos campos]** → usar defaults/opcionais e validar explicitamente apenas pedidos novos.
- **[Falha parcial na receita]** → criar receita e itens na mesma transação da venda; qualquer erro desfaz toda a confirmação.
- **[Exposição de histórico]** → endpoints de consulta filtram por perfil e atendente no backend; respostas não incluem credenciais ou dados fora da autorização.
- **[Complexidade da tela de atendimento]** → começar com inclusão de itens e fechamento em uma página, deixando relatórios avançados para mudança posterior.

## Migration Plan

1. Validar e publicar as alterações aditivas de schema e funções no workspace Xano de desenvolvimento.
2. Publicar endpoints protegidos de pedidos, confirmação e consulta.
3. Validar contratos de autorização, estoque, pagamento e controlados antes de habilitar a tela.
4. Compilar e testar o Reflex com os dois perfis.
5. Em caso de rollback, remover somente endpoints e telas novos; preservar campos e registros criados para não quebrar histórico.
