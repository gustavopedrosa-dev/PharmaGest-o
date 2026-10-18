## Why

O FarmaGestão já possui autenticação, consulta de estoque e cadastro de produtos, mas ainda não registra a operação principal da farmácia: o atendimento e a venda. Sem esse fluxo, o estoque não é baixado de forma vinculada a uma compra, não há rastreabilidade do atendente e as regras para medicamentos controlados não são aplicadas no momento da venda.

## What Changes

- Criar o fluxo de pedidos e vendas para colaboradores, com consulta para gestores.
- Permitir itens de pedido com produto, quantidade e preço praticado preservado no histórico.
- Registrar canal presencial ou online, funcionário atendente, cliente opcional e status do pedido.
- Confirmar vendas com forma de pagamento em dinheiro, cartão ou Pix.
- Reduzir o estoque transacionalmente somente quando a venda for confirmada.
- Bloquear vendas sem estoque suficiente ou com quantidade inválida.
- Exigir cliente cadastrado e número de receita para vendas que contenham medicamento controlado.
- Registrar a receita e os itens de receita mínimos necessários para rastreabilidade.
- Disponibilizar telas Reflex para registrar, consultar e visualizar vendas conforme o perfil.
- Manter vendas registradas imutáveis nas telas e preservar histórico de pedidos, itens, pagamentos e receitas.
- Manter fora do escopo lotes, validade, pedidos de compra, movimentação histórica de estoque, parcelas e cadastro detalhado da receita médica.

## Capabilities

### New Capabilities

- `vendas`: pedidos, confirmação de vendas, pagamentos, baixa de estoque e regras para medicamentos controlados.

### Modified Capabilities

- Nenhuma.

## Impact

- **Xano:** ajustes aditivos nas tabelas `pedido`, `item_pedido`, `venda`, `pagamento`, `receita` e `item_receita`; funções transacionais; endpoints protegidos para pedidos, vendas e consultas.
- **Reflex:** telas de atendimento e consulta de vendas, com ações condicionadas ao perfil.
- **Estoque:** integração da confirmação da venda com a baixa transacional já criada na Change `produtos-estoque`.
- **Autorização:** colaboradores registram pedidos e vendas; gestores consultam vendas; regras de negócio continuam aplicadas no backend.
- **Dados históricos:** pedidos, vendas, itens, pagamentos e receitas não serão apagados ou editados pelas telas.
