query "produtos/fornecedor" verb=POST {
  api_group = "Produtos"
  auth = "usuario"

  input {
    text nome filters=trim
    text cnpj filters=trim
    text? telefone
    email email
    text endereco filters=trim
    text? prazo_entrega?
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    precondition ($input.nome != "") {
      error_type = "inputerror"
      error = "O nome do fornecedor é obrigatório."
    }

    precondition ($input.cnpj != "") {
      error_type = "inputerror"
      error = "O CNPJ do fornecedor é obrigatório."
    }

    precondition ($input.endereco != "") {
      error_type = "inputerror"
      error = "O endereço do fornecedor é obrigatório."
    }

    db.query "fornecedor" {
      where = $db.fornecedor.cnpj == $input.cnpj
      return = {type: "single"}
      output = ["id"]
    } as $fornecedor_com_cnpj

    precondition ($fornecedor_com_cnpj == null) {
      error_type = "inputerror"
      error = "Já existe um fornecedor com este CNPJ."
    }

    db.add "fornecedor" {
      data = {
        nome: $input.nome,
        cnpj: $input.cnpj,
        telefone: $input.telefone,
        email: $input.email,
        endereco: $input.endereco,
        prazo_entrega: $input.prazo_entrega
      }
    } as $fornecedor
  }

  response = {fornecedor: $fornecedor}
  guid = "TGynrbFMc5kzcgpJNbTYbTMWUik"
}