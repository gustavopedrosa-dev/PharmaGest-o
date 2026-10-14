function "Identidade/require_active_role" {
  description = "Valida a conta atual e sua autorização no banco."

  input {
    text required_role?=""
  }

  stack {
    db.get "usuario" {
      field_name = "id"
      field_value = $auth.id
      output = ["id", "id_funcionario", "login", "perfil_acesso", "ativo"]
    } as $usuario

    precondition ($usuario != null) {
      error_type = "accessdenied"
      error = "Sessão inválida."
    }

    precondition ($usuario.ativo == true) {
      error_type = "accessdenied"
      error = "Sessão inválida."
    }

    precondition (
      $usuario.perfil_acesso == "gestor" || $usuario.perfil_acesso == "colaborador"
    ) {
      error_type = "accessdenied"
      error = "Sessão inválida."
    }

    conditional {
      if ($input.required_role != "") {
        precondition ($usuario.perfil_acesso == $input.required_role) {
          error_type = "accessdenied"
          error = "Você não tem permissão para esta ação"
        }
      }
    }

    db.get "funcionario" {
      field_name = "id"
      field_value = $usuario.id_funcionario
      output = ["id", "nome"]
    } as $funcionario
  }

  response = {
    id_usuario: $usuario.id,
    id_funcionario: $usuario.id_funcionario,
    login: $usuario.login,
    perfil_acesso: $usuario.perfil_acesso,
    nome: $funcionario.nome
  }
  history = false
  guid = "Rue-q9O6DDvmH5MqQaaAVbK_h9E"
}
