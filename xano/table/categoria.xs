table categoria {
  auth = false

  schema {
    int id
    text? nome
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "ativo", op: "asc"}]}
  ]
  tags = ["modulo produtos", "farmagestão"]
  guid = "3c2sACIyQLN_LiCvqdKqTbcdV9s"
}