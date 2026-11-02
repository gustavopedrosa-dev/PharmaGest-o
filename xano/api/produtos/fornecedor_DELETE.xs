query "produtos/fornecedor/{id}" verb=DELETE {
  api_group = "Produtos"
  auth = "usuario"

  input {
    int id
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    db.get "fornecedor" {
      field_name = "id"
      field_value = $input.id
      output = ["id"]
    } as $fornecedor

    precondition ($fornecedor != null) {
      error_type = "notfound"
      error = "Fornecedor não encontrado."
    }

    db.query "produto" {
      where = $db.produto.id_fornecedor == $input.id
      return = {type: "exists"}
    } as $produtos_vinculados

    precondition (!$produtos_vinculados) {
      error_type = "inputerror"
      error = "Não é possível remover um fornecedor vinculado a produtos."
    }

    db.del "fornecedor" {
      field_name = "id"
      field_value = $input.id
    }
  }

  response = {sucesso: true}
  guid = "LTNO_NZmawnCaEYJ_Qk-u1qraHc"
}