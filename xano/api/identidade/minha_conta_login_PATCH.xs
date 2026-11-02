query "identidade/minha-conta/login" verb=PATCH {
  api_group = "Identidade"
  auth = "usuario"

  input {
    text login filters=trim|lower
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "colaborador"}
    } as $sessao

    db.get "usuario" {
      field_name = "login"
      field_value = $input.login
      output = ["id"]
    } as $login_existente

    precondition (
      $login_existente == null || $login_existente.id == $auth.id
    ) {
      error_type = "inputerror"
      error = "Este login já está em uso."
    }

    db.edit "usuario" {
      field_name = "id"
      field_value = $auth.id
      data = {login: $input.login}
    } as $usuario_atualizado
  }

  response = {sessao: $sessao}
  guid = "q7tWerK6ovBz3qqdIe2PxjXUs5k"
}
