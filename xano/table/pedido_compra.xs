// Tabela: pedido_compra
table pedido_compra {
  auth = false

  schema {
    int id
    int id_fornecedor {
      table = "fornecedor"
    }
  
    timestamp? data_pedido
    enum? status {
      values = ["Concluído", "Em andamento", "Cancelado"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "id_fornecedor", op: "asc"}]}
  ]

  tags = ["modulo fornecedor ", "farmagestão"]
  guid = "rcVJW6Pk6DfZQ-vBNYMaW4vfA8Q"
}