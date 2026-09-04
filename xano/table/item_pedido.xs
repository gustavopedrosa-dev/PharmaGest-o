// Tabela: item_pedido
table item_pedido {
  auth = false

  schema {
    int id
    int id_pedido {
      table = "pedido"
    }
  
    int id_produto {
      table = "produto"
    }
  
    int id_item_receita? {
      table = "item_receita"
    }
  
    int quantidade
    decimal? valor_unitario
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "id_pedido", op: "asc"}]}
    {type: "btree", field: [{name: "id_produto", op: "asc"}]}
    {
      type : "btree"
      field: [{name: "id_item_receita", op: "asc"}]
    }
  ]

  tags = ["modulo pedidos", "modulo produtos", "farmagestão"]
  guid = "TJfdodrlqMD4GoSRBuGR8xw0Rlc"
}