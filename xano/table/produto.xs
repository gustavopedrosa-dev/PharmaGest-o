// Tabela: produto
table produto {
  auth = false

  schema {
    int id
    int id_categoria {
      table = "categoria"
    }
  
    int id_fornecedor {
      table = "fornecedor"
    }
  
    text? nome
    text? descricao
    text? codigo_barras
    bool? controlado
    decimal? preco_venda
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "id_categoria", op: "asc"}]}
    {type: "btree", field: [{name: "id_fornecedor", op: "asc"}]}
  ]

  tags = ["modulo produtos", "farmagestão"]
  guid = "wwzjpb7rr1oGkuLgEChunpWl35M"
}