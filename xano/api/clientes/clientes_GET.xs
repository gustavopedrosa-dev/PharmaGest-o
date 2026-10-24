query "clientes" verb=GET {
  api_group = "Clientes"
  auth = "usuario"

  input {
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: ""}
    } as $sessao

    db.query "cliente" {
      return = {type: "list"}
      output = [
        "id",
        "nome",
        "cpf",
        "data_nascimento",
        "telefone",
        "email",
        "data_cadastro",
        "ativo"
      ]
    } as $clientes
  }

  response = {clientes: $clientes}
  guid = "clientes-get"
}