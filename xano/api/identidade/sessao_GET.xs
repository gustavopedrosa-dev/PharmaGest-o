query "identidade/sessao" verb=GET {
  api_group = "Identidade"
  auth = "usuario"

  input {
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: ""}
    } as $sessao
  }

  response = {sessao: $sessao}
  guid = "d7MtJeMSSfqc2r5R-1JKAAcPknE"
}
