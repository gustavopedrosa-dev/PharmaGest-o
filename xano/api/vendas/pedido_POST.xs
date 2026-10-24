query "vendas/pedido" verb=POST {
  api_group = "Vendas"
  auth = "usuario"

  input {
    int? id_cliente
    enum canal {
      values = ["presencial", "online"]
    }
    json itens
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "colaborador"}
    } as $sessao

    precondition ($input.itens != null) {
      error_type = "inputerror"
      error = "Informe ao menos um item."
    }

    var $quantidade_itens_unicos {
      value = $input.itens|map:$$.id_produto|unique|count
    }

    precondition (($input.itens|count) == $quantidade_itens_unicos) {
      error_type = "inputerror"
      error = "O mesmo produto não pode aparecer duas vezes no pedido."
    }

    conditional {
      if ($input.id_cliente != null) {
        db.get "cliente" {
          field_name = "id"
          field_value = $input.id_cliente
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
        db.add "pedido" {
          data = {
            id_cliente: $input.id_cliente,
            id_funcionario: $sessao.id_funcionario,
            data_pedido: now,
            status: "pendente",
            canal: $input.canal
          }
        } as $pedido

        var $quantidade_itens { value = 0 }

        foreach ($input.itens) {
          each as $item {
            math.add $quantidade_itens { value = 1 }

            function.run "Vendas/validate_order_item" {
              input = {
                id_produto: $item.id_produto,
                quantidade: $item.quantidade
              }
            } as $validacao

            db.add "item_pedido" {
              data = {
                id_pedido: $pedido.id,
                id_produto: $item.id_produto,
                quantidade: $item.quantidade,
                valor_unitario: $validacao.produto.preco_venda
              }
            } as $item_criado
          }
        }

        precondition ($quantidade_itens > 0) {
          error_type = "inputerror"
          error = "Informe ao menos um item."
        }
      }
    }
  }

  response = {pedido: $pedido}
  guid = "vendas-pedido-post"
}
