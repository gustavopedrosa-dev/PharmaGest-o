query "vendas" verb=GET {
  api_group = "Vendas"
  auth = "usuario"

  input {
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    db.query "venda" {
      output = [
        "id",
        "id_pedido",
        "data_venda",
        "valor_total",
        "status"
      ]
    } as $vendas

    db.query "pagamento" {
      output = [
        "id",
        "id_venda",
        "forma_pagamento",
        "valor"
      ]
    } as $pagamentos
  }

  response = {
    vendas: $vendas,
    pagamentos: $pagamentos
  }
  guid = "vendas-get"
}
