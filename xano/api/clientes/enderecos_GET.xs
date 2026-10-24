query "clientes/cliente/{id}/enderecos" verb=GET {
  api_group = "Clientes"
  auth = "usuario"

  input {
    int id
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: ""}
    } as $sessao

    db.get "cliente" {
      field_name = "id"
      field_value = $input.id
      output = ["id"]
    } as $cliente

    precondition ($cliente != null) {
      error_type = "notfound"
      error = "Cliente não encontrado."
    }

    db.query "endereco" {
      where = $db.endereco.id_cliente == $input.id
      return = {type: "list"}
      output = [
        "id",
        "id_cliente",
        "logradouro",
        "numero",
        "bairro",
        "cidade",
        "estado",
        "cep",
        "complemento"
      ]
    } as $enderecos
  }

  response = {enderecos: $enderecos}
  guid = "enderecos-get"
}