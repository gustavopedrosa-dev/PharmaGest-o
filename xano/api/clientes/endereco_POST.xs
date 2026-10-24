query "clientes/cliente/{id}/endereco" verb=POST {
  api_group = "Clientes"
  auth = "usuario"

  input {
    int id
    text? logradouro filters=trim
    text? numero filters=trim
    text? bairro filters=trim
    text cidade filters=trim
    text estado filters=trim
    text? cep filters=trim
    text complemento filters=trim
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "colaborador"}
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

    db.add "endereco" {
      data = {
        id_cliente: $input.id,
        logradouro: $input.logradouro,
        numero: $input.numero,
        bairro: $input.bairro,
        cidade: $input.cidade,
        estado: $input.estado,
        cep: $input.cep,
        complemento: $input.complemento
      }
    } as $endereco
  }

  response = {endereco: $endereco}
  guid = "endereco-post"
}