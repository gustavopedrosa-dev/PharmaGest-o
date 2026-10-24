query "clientes/cliente" verb=POST {
  api_group = "Clientes"
  auth = "usuario"

  input {
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

        precondition ($cliente_com_cpf == null) {
          error_type = "inputerror"
          error = "O CPF já está cadastrado."
        }
      }
    }

    db.add "cliente" {
      data = {
        nome: $input.nome,
        cpf: $input.cpf,
        data_nascimento: $input.data_nascimento,
        telefone: $input.telefone,
        email: $input.email,
        data_cadastro: now,
        ativo: true
      }
    } as $cliente
  }

  response = {cliente: $cliente}
  guid = "cliente-post"
}