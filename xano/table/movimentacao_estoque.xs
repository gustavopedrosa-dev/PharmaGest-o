// Tabela: movimentacao_estoque
table movimentacao_estoque {
  auth = false

  schema {
    int id
    int id_lote {
      table = "lote"
    }
  
    int id_item_pedido? {
      table = "item_pedido"
    }
  
    int id_item_pedido_compra? {
      table = "item_pedido_compra"
    }
  
    text? tipo
    int? quantidade
    timestamp? data
    text motivo
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "id_lote", op: "asc"}]}
    {type: "btree", field: [{name: "id_item_pedido", op: "asc"}]}
    {
      type : "btree"
      field: [{name: "id_item_pedido_compra", op: "asc"}]
    }
  ]

  tags = ["modulo produtos", "farmagestão"]
  guid = "BTIUt9IHYhWJK80iP476uwmBZJA"
}