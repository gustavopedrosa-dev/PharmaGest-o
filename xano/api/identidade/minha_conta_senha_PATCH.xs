query "identidade/minha-conta/senha" verb=PATCH {
  api_group = "Identidade"
  auth = "usuario"

  input {
    text senha_atual
    text nova_senha
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "colaborador"}
    } as $sessao

    db.get "usuario" {
      field_name = "id"
      field_value = $auth.id
      output = ["senha_hash"]
    } as $usuario

    security.check_password {
      text_password = $input.senha_atual
      hash_password = $usuario.senha_hash
    } as $senha_confere

    precondition ($senha_confere) {
      error_type = "inputerror"
      error = "A senha atual está incorreta."
    }

    db.edit "usuario" {
      field_name = "id"
      field_value = $auth.id
      data = {senha_hash: $input.nova_senha}
    } as $usuario_atualizado
  }

  response = {sessao: $sessao}
  guid = "8Qx9o5uDJ7HdGEHasfTcZoRMbXY"
}
