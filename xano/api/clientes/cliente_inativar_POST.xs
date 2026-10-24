query "clientes/cliente/{id}/inativar" verb=POST {
  api_group = "Clientes"
  auth = "usuario"

  input {
    int id
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "colaborador"}
    } as $sessao

    db.get "cliente" {
      field_name = "id"
      field_value = $input.id
      output = ["id"]
    } as $cliente_existente

    precondition ($cliente_existente != null) {
      error_type = "notfound"
      error = "Cliente não encontrado."
    }

    db.edit "cliente" {
      field_name = "id"
      field_value = $input.id
      data = {ativo: false}
    } as $cliente
  }

  response = {cliente: $cliente}
  guid = "cliente-inativar-post"
}