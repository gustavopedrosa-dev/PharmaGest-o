query "equipe/funcionario/{id}/inativar" verb=POST {
  api_group = "Equipe"
  auth = "usuario"

  input {
    int id
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    db.get "funcionario" {
      field_name = "id"
      field_value = $input.id
      output = [
        "id",
        "nome",
        "cpf",
        "data_nascimento",
        "telefone",
        "email",
        "cargo",
        "salario",
        "endereco",
        "data_admissao"
      ]
    } as $funcionario_existente

    precondition ($funcionario_existente != null) {
      error_type = "notfound"
      error = "Funcionário não encontrado."
    }

    db.get "usuario" {
      field_name = "id_funcionario"
      field_value = $input.id
      output = ["id"]
    } as $usuario

    precondition ($usuario != null) {
      error_type = "notfound"
      error = "Usuário do funcionário não encontrado."
    }

    db.edit "usuario" {
      field_name = "id"
      field_value = $usuario.id
      data = {ativo: false}
    } as $usuario_inativado
  }

  response = {funcionario: $funcionario_existente, ativo: false}
  guid = "funcionario-inativar-post"
}