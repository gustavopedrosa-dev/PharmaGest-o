// Tabela: item_receita
table item_receita {
  auth = false

  schema {
    int id
    int id_receita {
      table = "receita"
    }
  
    int produto_id {
      table = "produto"
    }
  
    text? dosagem
    text? posologia
    int? quantidade_prescrita
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "id_receita", op: "asc"}]}
    {type: "btree", field: [{name: "produto_id", op: "asc"}]}
  ]

  tags = ["modulo cliente", "modulo produtos", "farmagestão"]
  guid = "nv-lxlY-gB1nowlmNssi6xbgXw4"
}