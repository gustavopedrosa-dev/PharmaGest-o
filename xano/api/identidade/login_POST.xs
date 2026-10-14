query "identidade/login" verb=POST {
  api_group = "Identidade"

  input {
    text login filters=trim|lower
    text senha
  }

  stack {
    db.get "usuario" {
      field_name = "login"
      field_value = $input.login
      output = ["id", "id_funcionario", "login", "senha_hash", "perfil_acesso", "ativo"]
    } as $usuario

    precondition ($usuario != null) {
      error_type = "accessdenied"
      error = "usuário ou senha inválidos"
    }

    precondition ($usuario.ativo == true) {
      error_type = "accessdenied"
      error = "usuário ou senha inválidos"
    }

    precondition (
      $usuario.perfil_acesso == "gestor" || $usuario.perfil_acesso == "colaborador"
    ) {
      error_type = "accessdenied"
      error = "usuário ou senha inválidos"
    }

    security.check_password {
      text_password = $input.senha
      hash_password = $usuario.senha_hash
    } as $senha_confere

    precondition ($senha_confere) {
      error_type = "accessdenied"
      error = "usuário ou senha inválidos"
    }

    db.get "funcionario" {
      field_name = "id"
      field_value = $usuario.id_funcionario
      output = ["id", "nome"]
    } as $funcionario

    security.create_auth_token {
      table = "usuario"
      extras = {}
      expiration = 28800
      id = $usuario.id
    } as $token
  }

  response = {
    token: $token,
    sessao: {
      id_usuario: $usuario.id,
      id_funcionario: $usuario.id_funcionario,
      nome: $funcionario.nome,
      login: $usuario.login,
      perfil_acesso: $usuario.perfil_acesso
    }
  }
  guid = "Kq3Vt6W6STmHFWDEyuUjTHHglVg"
}
