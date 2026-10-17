query "produtos/categoria/{id}/inativar" verb=POST {
  api_group = "Produtos"
  auth = "usuario"

  input {
    int id
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    db.get "categoria" {
      field_name = "id"
      field_value = $input.id
      output = ["id"]
    } as $categoria_existente

    precondition ($categoria_existente != null) {
      error_type = "notfound"
      error = "Categoria não encontrada."
    }

    db.edit "categoria" {
      field_name = "id"
      field_value = $input.id
      data = {ativo: false}
    } as $categoria
  }

  response = {categoria: $categoria}
  guid = "38sNsoaD_wAfsT00Z8v-VIJj108"
}
