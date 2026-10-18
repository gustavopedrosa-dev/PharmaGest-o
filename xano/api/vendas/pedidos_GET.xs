query "vendas/pedidos" verb=GET {
  api_group = "Vendas"
  auth = "usuario"

  input {
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    db.query "pedido" {
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
  guid = "khS3IKnCLHtdpIgU5SbGeXleFS0"
}
