query "equipe/funcionario/{id}" verb=PATCH {
  api_group = "Equipe"
  auth = "usuario"

  input {
    int id
    text nome filters=trim
    text cpf filters=trim
    date? data_nascimento
    text? telefone filters=trim
    email? email
    text? cargo filters=trim
    decimal? salario
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    db.get "funcionario" {
      field_name = "id"
      field_value = $input.id
      output = ["id"]
    } as $funcionario_existente

    precondition ($funcionario_existente != null) {
      error_type = "notfound"
      error = "Funcionário não encontrado."
    }

    db.get "funcionario" {
      field_name = "cpf"
      field_value = $input.cpf
      output = ["id"]
    } as $cpf_existente

    precondition ($cpf_existente == null || $cpf_existente.id == $input.id) {
      error_type = "inputerror"
      error = "O CPF já está cadastrado."
    }

    db.get "usuario" {
      field_name = "id_funcionario"
      field_value = $input.id
      output = ["ativo"]
    } as $usuario

    db.edit "funcionario" {
      field_name = "id"
      field_value = $input.id
      data = {
        nome: $input.nome,
        cpf: $input.cpf,
        data_nascimento: $input.data_nascimento,
        telefone: $input.telefone,
        email: $input.email,
        cargo: $input.cargo,
        salario: $input.salario
      }
    } as $funcionario
  }

  response = {funcionario: $funcionario, ativo: $usuario.ativo}
  guid = "funcionario-patch"
}