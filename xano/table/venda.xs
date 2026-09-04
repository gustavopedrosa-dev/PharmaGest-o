// Tabela: venda
table venda {
  auth = false

  schema {
    int id
    int id_pedido {
      table = "pedido"
    }
  
    timestamp? data_venda
    decimal? valor_total
    enum? status {
      values = ["concluída", "estornada"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [{name: "id_pedido", op: "asc"}]
    }
  ]

  tags = ["modulo de venda", "farmagestão"]
  guid = "Q8lDQ4eJ1oPkyb4a0xY-2kl07ds"
}