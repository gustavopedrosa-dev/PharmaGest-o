query "produtos/categorias" verb=GET {
  api_group = "Produtos"
  auth = "usuario"

  input {
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: ""}
    } as $sessao

    db.query "categoria" {
      where = $db.categoria.ativo == true
      output = ["id", "nome", "ativo"]
    } as $categorias
  }

  response = {categorias: $categorias}
  guid = "Cn-FKZIlOaWRmPOViWhESumAASU"
}
