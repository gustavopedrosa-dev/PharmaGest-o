query "equipe/funcionarios" verb=GET {
  api_group = "Equipe"
  auth = "usuario"

  input {
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    db.query "funcionario" {
      return = {type: "list"}
      output = [
        "id",
        "nome",
        "cpf",
        "data_nascimento",
        "telefone",
        "email",
        "cargo",
        "salario",
        "data_admissao"
      ]
    } as $funcionarios

    db.query "usuario" {
      return = {type: "list"}
      output = ["id_funcionario", "ativo"]
    } as $usuarios
  }

  response = {funcionarios: $funcionarios, usuarios: $usuarios}
  guid = "funcionarios-get"
}