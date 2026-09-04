table categoria {
  auth = false

  schema {
    int id
    text? nome
  }

  index = [{type: "primary", field: [{name: "id"}]}]
  tags = ["modulo produtos", "farmagestão"]
  guid = "3c2sACIyQLN_LiCvqdKqTbcdV9s"
}