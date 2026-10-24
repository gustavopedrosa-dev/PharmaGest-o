## Context

Consulte `proposal.md` para a motivação e `specs/clientes/spec.md` para o contrato comportamental. O projeto já possui autenticação por sessão, autorização no Xano, um adaptador HTTP server-side em `api/xano.py` e estado Reflex em `connectdrogs/connectdrogs.py`. A tabela `cliente` já existe no banco; o campo `ativo` é a única alteração estrutural necessária para esta change e deve ser aditivo, com padrão `true`.

## Goals / Non-Goals

**Goals:**

- Entregar o fluxo completo de clientes entre Xano e Reflex.
- Centralizar autorização e validação de situação do cliente no backend.
- Reutilizar o padrão de erros, sessão e transporte já adotado pelo frontend.
- Preservar pedidos e endereços vinculados quando um cliente for inativado.

**Non-Goals:**

- Criar login ou portal para clientes.
- Alterar vendas ou permitir edição de pedidos já registrados.
- Implementar fornecedores, funcionários, receitas ou novas regras de estoque.
- Excluir fisicamente clientes ou endereços.

## Decisions

1. **Usar inativação lógica para clientes.**
   O campo `cliente.ativo` será inicializado como `true`; a operação de inativar apenas muda esse valor para `false`. Isso mantém referências históricas e segue o modelo do projeto. Exclusão física foi considerada, mas é incompatível com o histórico de pedidos e com a regra de negócio.

2. **Aplicar autorização em endpoints Xano separados por operação.**
   Cada endpoint validará a sessão e o perfil antes de consultar ou alterar dados. A interface pode ocultar ações de acordo com o perfil, mas isso não será usado como controle de segurança. A alternativa de proteger apenas a tela foi descartada porque permitiria chamadas diretas indevidas à API.

3. **Manter endereços como registros vinculados à tabela `endereco`.**
   O cadastro de endereço receberá um `id_cliente` existente e as consultas retornarão somente endereços desse cliente. Não será criado um endereço embutido em `cliente`, pois o modelo permite vários endereços por cliente e já possui a relação correspondente.

4. **Adicionar operações ao adaptador Xano existente.**
   O Reflex usará métodos do `XanoClient` para listar, criar, editar e inativar clientes, além de listar e criar endereços. O tratamento de sessão expirada, proibição e indisponibilidade seguirá as exceções já existentes, evitando uma segunda convenção de comunicação.

5. **Usar uma única capability plana `clientes`.**
   Clientes e endereços formam um fluxo de cadastro único nesta change. Separá-los em changes independentes deixaria o cadastro sem a informação de endereço necessária ao domínio e aumentaria a integração entre branches.

## Risks / Trade-offs

- **[Risco]** Dados existentes podem não ter o novo campo `ativo` preenchido de forma uniforme. **Mitigação:** migração aditiva com padrão `true` e normalização no endpoint de leitura.
- **[Risco]** Um cliente inativo pode ser reutilizado por uma API de vendas que não valide a situação. **Mitigação:** a change deve expor a regra de cliente ativo para integração e a implementação de vendas deve validá-la no backend antes de criar novos pedidos.
- **[Trade-off]** A primeira versão não inclui edição ou remoção de endereços. **Mitigação:** manter o cadastro e a consulta suficientes para o fluxo inicial; tratar manutenção avançada em change posterior se for necessária.

## Migration Plan

1. Adicionar `cliente.ativo` no Xano com valor padrão `true` e publicar os endpoints protegidos.
2. Publicar os métodos do cliente HTTP e as telas Reflex.
3. Executar testes de contrato, autorização, inativação e vínculo de endereço.
4. Em caso de rollback, remover a exposição das novas telas e endpoints sem apagar clientes nem endereços; a coluna aditiva pode permanecer sem afetar as mudanças anteriores.