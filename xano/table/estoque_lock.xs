// Lock técnico transacional para serializar confirmações por produto.
table estoque_lock {
  auth = false

  schema {
    int id
    int id_produto {
      table = "produto"
    }
    enum status {
      values = ["ativo", "liberado"]
    }
    timestamp criado_em
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [
        {name: "id_produto", op: "asc"}
        {name: "status", op: "asc"}
      ]
    }
  ]

  tags = ["modulo de venda", "farmagestão", "tecnico"]
  guid = "vendas-estoque-lock"
}
