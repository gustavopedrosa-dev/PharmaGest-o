table receita {
  auth = false

  schema {
    int id
    int id_cliente {
      table = "cliente"
    }
  
    text? nome_medico
    text? crm_medico
    date? data_emissao
    date? data_validade
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "id_cliente", op: "asc"}]}
  ]

  tags = ["modulo produtos", "farmagestão", "modulo cliente"]
  guid = "1yiS-7Uso-s16xIDbUOvEECCvuU"
}