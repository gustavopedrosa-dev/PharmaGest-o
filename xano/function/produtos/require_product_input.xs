function "Produtos/require_product_input" {
  description = "Valida os dados de cadastro e atualização de um produto."

  input {
    int id_categoria
    int id_fornecedor
    text nome filters=trim
    decimal preco_venda
    int quantidade_estoque
    int estoque_minimo
  }

  stack {
    precondition ($input.nome != "") {
      error_type = "inputerror"
      error = "O nome do produto é obrigatório."
    }

    precondition ($input.preco_venda >= 0) {
      error_type = "inputerror"
      error = "O preço de venda não pode ser negativo."
    }

    precondition ($input.quantidade_estoque >= 0) {
      error_type = "inputerror"
      error = "A quantidade em estoque não pode ser negativa."
    }

    precondition ($input.estoque_minimo >= 0) {
      error_type = "inputerror"
      error = "O estoque mínimo não pode ser negativo."
    }

    db.get "categoria" {
      field_name = "id"
      field_value = $input.id_categoria
      output = ["id", "ativo"]
    } as $categoria

    precondition ($categoria != null && $categoria.ativo == true) {
      error_type = "inputerror"
      error = "A categoria informada não está disponível."
    }

    db.get "fornecedor" {
      field_name = "id"
      field_value = $input.id_fornecedor
      output = ["id"]
    } as $fornecedor

    precondition ($fornecedor != null) {
      error_type = "inputerror"
      error = "O fornecedor informado não existe."
    }
  }

  response = {valid: true}
  history = false
  guid = "sNnxOne-Yq8vZ_J2IwEzlFZ9UaA"
}
