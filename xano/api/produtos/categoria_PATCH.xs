query "produtos/categoria/{id}" verb=PATCH {
  api_group = "Produtos"
  auth = "usuario"

  input {
    int id
    text nome filters=trim
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    precondition ($input.nome != "") {
      error_type = "inputerror"
      error = "O nome da categoria é obrigatório."
    }

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
      data = {nome: $input.nome}
    } as $categoria
  }

  response = {categoria: $categoria}
  guid = "w1xIICyVTd_pVPaBsP1Zwcy8y3g"
}
