query "vendas/meus-pedidos" verb=GET {
  api_group = "Vendas"
  auth = "usuario"

  input {
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "colaborador"}
    } as $sessao

    db.query "pedido" {
      where = $db.pedido.id_funcionario == $sessao.id_funcionario
      return = {type: "list"}
      output = [
        "id",
        "id_cliente",
        "id_funcionario",
        "data_pedido",
        "status",
        "canal"
      ]
    } as $pedidos

    db.query "item_pedido" {
      where = $db.item_pedido.id_pedido in ($pedidos|map:"id")
      return = {type: "list"}
      output = [
        "id",
        "id_pedido",
        "id_produto",
        "quantidade",
        "valor_unitario"
      ]
    } as $itens
  }

  response = {
    pedidos: $pedidos,
    itens: $itens
  }
  guid = "qTxZlUikZYPjBFiiInMb5hy_ylE"
}
