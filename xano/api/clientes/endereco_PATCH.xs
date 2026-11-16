query "clientes/cliente/{id}/endereco/{endereco_id}" verb=PATCH {
  api_group = "Clientes"
  auth = "usuario"

  input {
    int id
    int endereco_id
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

    db.get "endereco" {
      field_name = "id"
      field_value = $input.endereco_id
      output = ["id", "id_cliente"]
    } as $endereco_existente

    precondition (
      $endereco_existente != null && $endereco_existente.id_cliente == $input.id
    ) {
      error_type = "notfound"
      error = "Endereço não encontrado para este cliente."
    }

    db.edit "endereco" {
      field_name = "id"
      field_value = $input.endereco_id
      data = {
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
  guid = "endereco-patch"
}
