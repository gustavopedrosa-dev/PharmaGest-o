query "clientes/cliente/{id}" verb=PATCH {
  api_group = "Clientes"
  auth = "usuario"

  input {
    int id
    text nome filters=trim
    text? cpf filters=trim
    date data_nascimento
    text? telefone filters=trim
    email? email
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

    precondition ($input.nome != "") {
      error_type = "inputerror"
      error = "O nome do cliente é obrigatório."
    }

    conditional {
      if ($input.cpf != null && $input.cpf != "") {
        db.get "cliente" {
          field_name = "cpf"
          field_value = $input.cpf
          output = ["id"]
        } as $cliente_com_cpf

        precondition (
          $cliente_com_cpf == null || $cliente_com_cpf.id == $input.id
        ) {
          error_type = "inputerror"
          error = "O CPF já está cadastrado."
        }
      }
    }

    db.edit "cliente" {
      field_name = "id"
      field_value = $input.id
      data = {
        nome: $input.nome,
        cpf: $input.cpf,
        data_nascimento: $input.data_nascimento,
        telefone: $input.telefone,
        email: $input.email
      }
    } as $cliente
  }

  response = {cliente: $cliente}
  guid = "cliente-patch"
}