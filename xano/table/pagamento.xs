// Tabela: pagamento
table pagamento {
  auth = false

  schema {
    int id
    int id_venda {
      table = "venda"
    }
  
    enum? forma_pagamento {
      values = ["dinheiro", "cartão", "pix", "convênio"]
    }
  
    decimal? valor
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "id_venda", op: "asc"}]}
  ]

  tags = ["modulo de venda", "farmagestão"]
  guid = "rZp_oCmKncTM20G7xWO6veeOyAw"
}