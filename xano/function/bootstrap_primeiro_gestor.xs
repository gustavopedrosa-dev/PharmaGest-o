function bootstrap_primeiro_gestor {
  description = "Provisiona uma única vez o primeiro funcionário Gestor e sua conta."

  input {
    text nome filters=trim
    text cpf filters=trim
    text login filters=trim
    text senha
  }

  stack {
    db.transaction {
      stack {
        db.query "usuario" {
          where = $db.usuario.perfil_acesso == "gestor"
          return = {type: "exists"}
        } as $gestor_existe

        precondition (!$gestor_existe) {
          error_type = "inputerror"
          error = "O bootstrap do gestor já foi realizado."
        }

        db.add "funcionario" {
          data = {
            nome: $input.nome,
            cpf: $input.cpf,
            cargo: "Gestor",
            data_admissao: now
          }
        } as $funcionario

        db.add "usuario" {
          data = {
            id_funcionario: $funcionario.id,
            login: $input.login,
            senha_hash: $input.senha,
            perfil_acesso: "gestor",
            ativo: true
          }
        } as $usuario_criado
      }
    }
  }

  response = {status: "created"}
  history = false
  guid = "LksVeKaOExJHy1d-QIQ_gYwSaz0"
}
