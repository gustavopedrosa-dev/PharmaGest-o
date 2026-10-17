function "Produtos/decrease_stock" {
  description = "Reduz o estoque de um produto sem permitir saldo negativo."

  input {
    int id_produto
    int quantidade
  }

  stack {
    precondition ($input.quantidade > 0) {
      error_type = "inputerror"
      error = "A quantidade vendida deve ser positiva."
    }

    db.transaction {
      stack {
        db.get "produto" {
          field_name = "id"
          field_value = $input.id_produto
          output = ["id", "quantidade_estoque", "ativo"]
        } as $produto

        precondition ($produto != null && $produto.ativo == true) {
          error_type = "inputerror"
          error = "O produto não está disponível para venda."
        }

        precondition ($produto.quantidade_estoque >= $input.quantidade) {
          error_type = "inputerror"
          error = "Estoque insuficiente."
        }

        db.edit "produto" {
          field_name = "id"
          field_value = $input.id_produto
          data = {
            quantidade_estoque: $produto.quantidade_estoque - $input.quantidade
          }
        } as $produto_atualizado
      }
    }
  }

  response = {
    id_produto: $produto_atualizado.id,
    quantidade_estoque: $produto_atualizado.quantidade_estoque
  }
  history = false
  guid = "_tL2drnCdotvXscBKOkpW3xf_sI"
}
