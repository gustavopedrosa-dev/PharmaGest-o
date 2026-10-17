query "produtos/produto/{id}" verb=PATCH {
  api_group = "Produtos"
  auth = "usuario"

  input {
    int id
    int id_categoria
    int id_fornecedor
    text nome filters=trim
    text? descricao filters=trim
    text? codigo_barras filters=trim
    bool? controlado
    decimal preco_venda
    int quantidade_estoque
    int estoque_minimo
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    db.get "produto" {
      field_name = "id"
      field_value = $input.id
      output = ["id"]
    } as $produto_existente

    precondition ($produto_existente != null) {
      error_type = "notfound"
      error = "Produto não encontrado."
    }

    function.run "Produtos/require_product_input" {
      input = {
        id_categoria: $input.id_categoria,
        id_fornecedor: $input.id_fornecedor,
        nome: $input.nome,
        preco_venda: $input.preco_venda,
        quantidade_estoque: $input.quantidade_estoque,
        estoque_minimo: $input.estoque_minimo
      }
    } as $validacao

    db.edit "produto" {
      field_name = "id"
      field_value = $input.id
      data = {
        id_categoria: $input.id_categoria,
        id_fornecedor: $input.id_fornecedor,
        nome: $input.nome,
        descricao: $input.descricao,
        codigo_barras: $input.codigo_barras,
        controlado: $input.controlado,
        preco_venda: $input.preco_venda,
        quantidade_estoque: $input.quantidade_estoque,
        estoque_minimo: $input.estoque_minimo
      }
    } as $produto_atualizado
  }

  response = {produto: $produto_atualizado}
  guid = "IF3yUoZchzcV1tLK-VZ3lQH501g"
}
