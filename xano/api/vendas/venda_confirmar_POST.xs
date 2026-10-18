query "vendas/pedido/{id}/confirmar" verb=POST {
  api_group = "Vendas"
  auth = "usuario"

  input {
    int id
    enum forma_pagamento {
      values = ["dinheiro", "cartão", "pix"]
    }
    text? numero_receita filters=trim
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "colaborador"}
    } as $sessao

    db.get "pedido" {
      field_name = "id"
      field_value = $input.id
      output = [
        "id",
        "id_cliente",
        "id_funcionario",
        "status",
        "canal"
      ]
    } as $pedido

    precondition ($pedido != null) {
      error_type = "notfound"
      error = "Pedido não encontrado."
    }

    precondition (
      $pedido.id_funcionario == $sessao.id_funcionario &&
      $pedido.status == "pendente"
    ) {
      error_type = "accessdenied"
      error = "O pedido não está disponível para este atendimento."
    }

    db.query "item_pedido" {
      where = $db.item_pedido.id_pedido == $input.id
      output = [
        "id",
        "id_pedido",
        "id_produto",
        "quantidade",
        "valor_unitario"
      ]
    } as $itens

    precondition ($itens != null) {
      error_type = "inputerror"
      error = "O pedido precisa ter itens."
    }

    var $total { value = 0 }
    var $tem_controlado { value = false }
    var $quantidade_itens { value = 0 }

    foreach ($itens) {
      each as $item {
        math.add $quantidade_itens { value = 1 }
        db.get "produto" {
          field_name = "id"
          field_value = $item.id_produto
          output = [
            "id",
            "controlado",
            "ativo",
            "quantidade_estoque"
          ]
        } as $produto

        precondition (
          $produto != null &&
          $produto.ativo == true &&
          $produto.quantidade_estoque >= $item.quantidade
        ) {
          error_type = "inputerror"
          error = "Estoque insuficiente ou produto indisponível."
        }

        var $subtotal { value = $item.valor_unitario }
        math.mul $subtotal { value = $item.quantidade }
        math.add $total { value = $subtotal }

        conditional {
          if ($produto.controlado == true) {
            var.update $tem_controlado { value = true }
          }
        }
      }
    }

    precondition ($quantidade_itens > 0) {
      error_type = "inputerror"
      error = "O pedido precisa ter itens."
    }

    conditional {
      if ($tem_controlado == true) {
        precondition (
          $pedido.id_cliente != null &&
          $input.numero_receita != null &&
          $input.numero_receita != ""
        ) {
          error_type = "inputerror"
          error = "Venda controlada exige cliente e número da receita."
        }

        db.get "cliente" {
          field_name = "id"
          field_value = $pedido.id_cliente
          output = ["id", "ativo"]
        } as $cliente

        precondition ($cliente != null && $cliente.ativo == true) {
          error_type = "inputerror"
          error = "O cliente não está ativo."
        }
      }
    }

    db.transaction {
      stack {
        foreach ($itens) {
          each as $item {
            db.get "produto" {
              field_name = "id"
              field_value = $item.id_produto
              output = ["id", "quantidade_estoque", "ativo"]
            } as $produto_atual

            precondition (
              $produto_atual != null &&
              $produto_atual.ativo == true &&
              $produto_atual.quantidade_estoque >= $item.quantidade
            ) {
              error_type = "inputerror"
              error = "Estoque insuficiente ou produto indisponível."
            }

            db.edit "produto" {
              field_name = "id"
              field_value = $item.id_produto
              data = {
                quantidade_estoque: $produto_atual.quantidade_estoque - $item.quantidade
              }
            } as $produto_baixado
          }
        }

        db.add "venda" {
          data = {
            id_pedido: $pedido.id,
            id_funcionario: $sessao.id_funcionario,
            data_venda: now,
            valor_total: $total,
            status: "concluída"
          }
        } as $venda

        db.add "pagamento" {
          data = {
            id_venda: $venda.id,
            id_funcionario: $sessao.id_funcionario,
            forma_pagamento: $input.forma_pagamento,
            valor: $total
          }
        } as $pagamento

        conditional {
          if ($tem_controlado == true) {
            db.add "receita" {
              data = {
                id_cliente: $pedido.id_cliente,
                numero_receita: $input.numero_receita
              }
            } as $receita

            foreach ($itens) {
              each as $item_receita {
                db.get "produto" {
                  field_name = "id"
                  field_value = $item_receita.id_produto
                  output = ["id", "controlado"]
                } as $produto_receita

                conditional {
                  if ($produto_receita.controlado == true) {
                    db.add "item_receita" {
                      data = {
                        id_receita: $receita.id,
                        produto_id: $item_receita.id_produto,
                        quantidade_prescrita: $item_receita.quantidade
                      }
                    } as $item_receita_criado
                  }
                }
              }
            }
          }
        }

        db.edit "pedido" {
          field_name = "id"
          field_value = $pedido.id
          data = {status: "confirmado"}
        } as $pedido_confirmado
      }
    }
  }

  response = {
    venda: $venda,
    pagamento: $pagamento,
    total: $total
  }
  guid = "vendas-confirmar-post"
}
