table endereco {
  auth = false

  schema {
    int id
    int id_cliente {
      table = "cliente"
    }
  
    text? logradouro
    text? numero
    text? bairro
    text cidade
    text estado
    text? cep
    text complemento
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "id_cliente", op: "asc"}]}
  ]

  tags = ["modulo cliente", "farmagestão"]
  guid = "ElN7nOk5ElLjNQrGy4cLRyXyaLc"
}