table usuario {
  auth = false

  schema {
    int id
    int id_funcionario {
      table = "funcionario"
    }
  
    text login
    text? senha_hash
    enum? perfil_acesso {
      values = ["admin", "atendente", "farmacêutico", "gerente"]
    }
  
    bool? ativo
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [{name: "id_funcionario", op: "asc"}]
    }
    {type: "btree|unique", field: [{name: "login", op: "asc"}]}
    {
      type : "btree|unique"
      field: [{name: "senha_hash", op: "asc"}]
    }
  ]

  guid = "FmEeyG0mupdPTVqTey-6a3QVtx8"
}