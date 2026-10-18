function "Vendas/validate_order_item" {
  description = "Valida um item de pedido e retorna o produto ativo."

  input {
    int id_produto
    int quantidade
  }

  stack {
    precondition ($input.quantidade > 0) {
      error_type = "inputerror"
      error = "A quantidade do item deve ser positiva."
    }

    db.get "produto" {
      field_name = "id"
      field_value = $input.id_produto
      output = [
        "id",
        "nome",
        "preco_venda",
        "controlado",
        "quantidade_estoque",
        "ativo"
      ]
    } as $produto

    precondition ($produto != null && $produto.ativo == true) {
      error_type = "inputerror"
      error = "O produto não está disponível para venda."
    }
  }

  response = {produto: $produto}
  history = false
  guid = "vRcuJTRs0v1aT5504VNa6baTilc"
}
