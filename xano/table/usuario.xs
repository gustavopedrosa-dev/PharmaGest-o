table usuario {
  auth = true

  schema {
    int id
    int id_funcionario {
      table = "funcionario"
    }
  
    text login
    password senha_hash
    enum perfil_acesso {
      values = ["gestor", "colaborador"]
    }
  
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [{name: "id_funcionario", op: "asc"}]
    }
    {type: "btree|unique", field: [{name: "login", op: "asc"}]}
  ]

  guid = "FmEeyG0mupdPTVqTey-6a3QVtx8"
}