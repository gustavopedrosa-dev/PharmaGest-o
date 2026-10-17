query "produtos/estoque/baixa" verb=POST {
  api_group = "Produtos"
  auth = "usuario"

  input {
    int id_produto
    int quantidade
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    function.run "Produtos/decrease_stock" {
      input = {
        id_produto: $input.id_produto,
        quantidade: $input.quantidade
      }
    } as $resultado
  }

  response = $resultado
  guid = "X4-7csHip0LSU6bXoBRV7z0SHfU"
}
