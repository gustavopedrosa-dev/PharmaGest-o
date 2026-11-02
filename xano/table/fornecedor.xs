table fornecedor {
  auth = false

  schema {
    int id
    text? nome
    text? cnpj
    text? telefone
    email email
    text endereco
    text? prazo_entrega
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "cnpj", op: "asc"}]}
  ]

  tags = ["modulo fornecedor ", "farmagestão", "modulo produtos"]
  guid = "6uQx6eILwYbuzxt1O9SLZlUJN2c"
}