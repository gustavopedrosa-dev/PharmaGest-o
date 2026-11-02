query "painel/resumo" verb=GET {
  api_group = "Vendas"
  auth = "usuario"

  input {
    timestamp data_inicio
    timestamp data_fim
  }

  stack {
    function.run "Identidade/require_active_role" {
      input = {required_role: "gestor"}
    } as $sessao

    precondition ($input.data_inicio < $input.data_fim) {
      error_type = "inputerror"
      error = "O período informado é inválido."
    }

    db.query "venda" {
      where = $db.venda.status == "concluída" && $db.venda.data_venda >= $input.data_inicio && $db.venda.data_venda < $input.data_fim
      output = ["id", "id_pedido", "valor_total"]
    } as $vendas

    db.query "item_pedido" {
      join = {
        venda: {
          table: "venda",
          type: "inner",
          where: $db.item_pedido.id_pedido == $db.venda.id_pedido
        }
      }
      where = $db.venda.status == "concluída" && $db.venda.data_venda >= $input.data_inicio && $db.venda.data_venda < $input.data_fim
      output = ["id_produto", "quantidade"]
    } as $itens_vendidos

    db.query "produto" {
      output = ["id", "nome", "quantidade_estoque", "estoque_minimo", "ativo"]
    } as $produtos

    db.query "usuario" {
      where = $db.usuario.ativo == true
      return = {type: "count"}
    } as $funcionarios_ativos

    var $estoque_critico { value = [] }
    foreach ($produtos) {
      each as $produto {
        conditional {
          if (
            $produto.ativo == true &&
            $produto.quantidade_estoque <= $produto.estoque_minimo
          ) {
            array.push $estoque_critico {
              value = {
                id: $produto.id,
                nome: $produto.nome,
                estoque: $produto.quantidade_estoque,
                minimo: $produto.estoque_minimo
              }
            }
          }
        }
      }
    }

    var $mais_vendidos { value = [] }
    foreach ($produtos) {
      each as $produto {
        var $quantidade_vendida { value = 0 }
        foreach ($itens_vendidos) {
          each as $item {
            conditional {
              if ($item.id_produto == $produto.id) {
                math.add $quantidade_vendida { value = $item.quantidade }
              }
            }
          }
        }
        conditional {
          if ($quantidade_vendida > 0) {
            array.push $mais_vendidos {
              value = {
                id: $produto.id,
                nome: $produto.nome,
                quantidade: $quantidade_vendida
              }
            }
          }
        }
      }
    }

    var $total_vendas { value = $vendas|count }
    var $valor_total { value = $vendas|map:$$.valor_total|sum }
    var $mais_vendidos_ordenados {
      value = $mais_vendidos|sort:"quantidade":"int":true
    }
  }

  response = {
    total_vendas: $total_vendas,
    valor_total: $valor_total,
    funcionarios_ativos: $funcionarios_ativos,
    estoque_critico: $estoque_critico,
    mais_vendidos: $mais_vendidos_ordenados
  }
  guid = "x8lezje8pqphHrqn37aTu1EaVEI"
}