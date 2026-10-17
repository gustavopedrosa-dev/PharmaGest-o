query "produtos/estoque" verb=GET {
  api_group = "Produtos"
  auth = "usuario"

  input {
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: ""}
    } as $sessao

    db.query "produto" {
      where = $db.produto.ativo == true
      output = [
        "id",
        "id_categoria",
        "id_fornecedor",
        "nome",
        "descricao",
        "codigo_barras",
        "controlado",
        "preco_venda",
        "quantidade_estoque",
        "estoque_minimo",
        "ativo"
      ]
    } as $produtos
  }

  response = {
    produtos: $produtos
  }
  guid = "zWgvLHMDzL8asUOnLOyryklR4Vk"
}
