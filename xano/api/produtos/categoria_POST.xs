query "produtos/categoria" verb=POST {
  api_group = "Produtos"
  auth = "usuario"

  input {
    text nome filters=trim
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    precondition ($input.nome != "") {
      error_type = "inputerror"
      error = "O nome da categoria é obrigatório."
    }

    db.add "categoria" {
      data = {
        nome: $input.nome,
        ativo: true
      }
    } as $categoria
  }

  response = {categoria: $categoria}
  guid = "j7-tq5Dp-An15ZEz_q79NcGt7oc"
}
