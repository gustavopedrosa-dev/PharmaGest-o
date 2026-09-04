// Tabela: lote
table lote {
  auth = false

  schema {
    int id
    int id_produto {
      table = "produto"
    }
  
    text? numero_lote
    date? data_fabricacao
    date data_validade
    int? quantidade_atual
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "id_produto", op: "asc"}]}
  ]

  tags = ["modulo produtos", "farmagestão"]
  guid = "vJHeBMe5kzhdAP_bXf9Hv9qhJ9k"
}