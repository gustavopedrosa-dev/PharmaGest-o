table pedido {
  auth = false

  schema {
    int id
    int id_cliente {
      table = "cliente"
    }
  
    int id_funcionario {
      table = "funcionario"
    }
  
    timestamp data_pedido
    enum? status {
      values = ["pendente", "confirmado", "cancelado"]
    }
    enum? canal {
      values = ["presencial", "online"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "id_cliente", op: "asc"}]}
    {type: "btree", field: [{name: "id_funcionario", op: "asc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}]}
    {type: "btree", field: [{name: "canal", op: "asc"}]}
  ]

  tags = [
    "modulo pedidos"
    "modulo cliente"
    "modulo funcionarios"
    "modulo de venda"
    "farmagestão"
    "modulo produtos"
  ]

  guid = "rLCSxwdkUIkR6ASF6E4_rWip-z0"
}