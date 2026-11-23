query "equipe/funcionario" verb=POST {
  api_group = "Equipe"
  auth = "usuario"

  input {
    text nome filters=trim
    text cpf filters=trim
    date? data_nascimento
    text? telefone filters=trim
    email? email
    text? cargo filters=trim
    decimal? salario
    text? endereco filters=trim
    text login filters=trim|lower
    text? senha_inicial filters=trim
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    precondition ($input.nome != "") {
      error_type = "inputerror"
      error = "O nome do funcionário é obrigatório."
    }

    precondition ($input.cpf != "") {
      error_type = "inputerror"
      error = "O CPF do funcionário é obrigatório."
    }

    precondition ($input.login != "") {
      error_type = "inputerror"
      error = "O login do funcionário é obrigatório."
    }

    db.get "funcionario" {
      field_name = "cpf"
      field_value = $input.cpf
      output = ["id"]
    } as $cpf_existente

    precondition ($cpf_existente == null) {
      error_type = "inputerror"
      error = "O CPF já está cadastrado."
    }

    db.get "usuario" {
      field_name = "login"
      field_value = $input.login
      output = ["id"]
    } as $login_existente

    precondition ($login_existente == null) {
      error_type = "inputerror"
      error = "Este login já está em uso."
    }

    var $senha_escolhida { value = null }

    conditional {
      if ($input.senha_inicial != null && $input.senha_inicial != "") {
        var.update $senha_escolhida { value = $input.senha_inicial }
      }
      else {
        security.create_password {
          character_count = 12
          require_lowercase = true
          require_uppercase = true
          require_digit = true
          require_symbol = true
          symbol_whitelist = "!@#$%"
        } as $senha_gerada

        var.update $senha_escolhida { value = $senha_gerada }
      }
    }

    db.transaction {
      stack {
        db.add "funcionario" {
          data = {
            nome: $input.nome,
            cpf: $input.cpf,
            data_nascimento: $input.data_nascimento,
            telefone: $input.telefone,
            email: $input.email,
            cargo: $input.cargo,
            salario: $input.salario,
            endereco: $input.endereco,
            data_admissao: now
          }
        } as $funcionario

        db.add "usuario" {
          data = {
            id_funcionario: $funcionario.id,
            login: $input.login,
            senha_hash: $senha_escolhida,
            perfil_acesso: "colaborador",
            ativo: true
          }
        } as $usuario
      }
    }
  }

  response = {
    funcionario: $funcionario,
    acesso: {
      login: $input.login,
      senha_inicial: $senha_escolhida
    }
  }
  guid = "funcionario-post"
}