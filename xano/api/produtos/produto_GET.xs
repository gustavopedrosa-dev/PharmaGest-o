query "produtos/produto/{id}" verb=GET {
  api_group = "Produtos"
  auth = "usuario"

  input {
    int id
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: ""}
    } as $sessao

    db.get "produto" {
      field_name = "id"
      field_value = $input.id
      output = [
        "id",
        "id_categoria",
        "id_fornecedor",
        "nome",
        "descricao",
        "codigo_barras",
        "controlado",
        "preco_venda",
        "quantidade_estoque",
        "estoque_minimo",
        "ativo"
      ]
    } as $produto

    precondition ($produto != null) {
      error_type = "notfound"
      error = "Produto não encontrado."
    }
  }

  response = {produto: $produto}
  guid = "o_MrVIxPYOgWxMTTIwM5ofXf8lA"
}
