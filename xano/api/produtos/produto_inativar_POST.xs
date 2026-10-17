query "produtos/produto/{id}/inativar" verb=POST {
  api_group = "Produtos"
  auth = "usuario"

  input {
    int id
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    db.get "produto" {
      field_name = "id"
      field_value = $input.id
      output = ["id"]
    } as $produto_existente

    precondition ($produto_existente != null) {
      error_type = "notfound"
      error = "Produto não encontrado."
    }

    db.edit "produto" {
      field_name = "id"
      field_value = $input.id
      data = {ativo: false}
    } as $produto
  }

  response = {produto: $produto}
  guid = "TvugaS7QR3JBCd5ShXvTyLwkiaU"
}
