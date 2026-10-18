query "vendas/minhas" verb=GET {
  api_group = "Vendas"
  auth = "usuario"

  input {
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "colaborador"}
    } as $sessao

    db.query "venda" {
      where = $db.venda.id_funcionario == $sessao.id_funcionario
      output = [
        "id",
        "id_pedido",
        "data_venda",
        "valor_total",
        "status"
      ]
    } as $vendas

    db.query "pagamento" {
      where = $db.pagamento.id_funcionario == $sessao.id_funcionario
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
  guid = "vendas-minhas-get"
}
