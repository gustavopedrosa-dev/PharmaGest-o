query "equipe/funcionario/{id}/ativar" verb=POST {
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
      data = {ativo: true}
    } as $usuario_ativado
  }

  response = {funcionario: $funcionario_existente, ativo: true}
  guid = "funcionario-ativar-post"
}
