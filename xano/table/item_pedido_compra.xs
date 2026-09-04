// Tabela: item_pedido_compra
table item_pedido_compra {
  auth = false

  schema {
    int id
    int id_produto {
      table = "produto"
    }
  
    int id_pedido_compra {
      table = "pedido_compra"
    }
  
    int? quantidade
    decimal? valor_unitario
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "id_produto", op: "asc"}]}
    {
      type : "btree"
      field: [{name: "id_pedido_compra", op: "asc"}]
    }
  ]

  tags = ["modulo fornecedor ", "modulo produtos", "farmagestão"]
  guid = "Tz-4Y-rBXPl31A9Th80ek_pTKF8"
}