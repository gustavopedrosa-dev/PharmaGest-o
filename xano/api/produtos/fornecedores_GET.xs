query "produtos/fornecedores" verb=GET {
  api_group = "Produtos"
  auth = "usuario"

  input {
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    db.query "fornecedor" {
      output = [
        "id",
        "nome",
        "cnpj",
        "telefone",
        "email",
        "endereco",
        "prazo_entrega"
      ]
    } as $fornecedores
  }

  response = {fornecedores: $fornecedores}
  guid = "WurgKedB7Jfckz76uQG5SxElCsA"
}