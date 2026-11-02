query "produtos/fornecedor/{id}" verb=PATCH {
  api_group = "Produtos"
  auth = "usuario"

  input {
    int id
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

    db.get "fornecedor" {
      field_name = "id"
      field_value = $input.id
      output = ["id"]
    } as $fornecedor_existente

    precondition ($fornecedor_existente != null) {
      error_type = "notfound"
      error = "Fornecedor não encontrado."
    }

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
      where = $db.fornecedor.cnpj == $input.cnpj && $db.fornecedor.id != $input.id
      return = {type: "single"}
      output = ["id"]
    } as $outro_fornecedor_com_cnpj

    precondition ($outro_fornecedor_com_cnpj == null) {
      error_type = "inputerror"
      error = "Já existe um fornecedor com este CNPJ."
    }

    db.edit "fornecedor" {
      field_name = "id"
      field_value = $input.id
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
  guid = "GtNETA9rHTMy2KkTABiELuMnmhc"
}