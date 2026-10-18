table cliente {
  auth = false

  schema {
    int id
    text nome
    text? cpf
    date data_nascimento
    text? telefone
    email? email
    timestamp data_cadastro
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "cpf", op: "asc"}]}
    {type: "btree", field: [{name: "ativo", op: "asc"}]}
  ]

  tags = ["modulo cliente", "farmagestão", "modulo pedidos"]
  guid = "W7aR6Hre4un2WuNZNhvucxVeXV4"
}