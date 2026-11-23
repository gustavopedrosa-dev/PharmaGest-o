table funcionario {
  auth = false

  schema {
    int id
    text nome
    text cpf
    date? data_nascimento
    text? telefone
    email? email
    text? cargo
    decimal? salario
    text? endereco
    timestamp data_admissao
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "cpf", op: "asc"}]}
  ]

  tags = ["modulo funcionarios", "farmagestão", "modulo pedidos"]
  guid = "1jPcMMkDuqdFUO5LmX72ePaZS7o"
}