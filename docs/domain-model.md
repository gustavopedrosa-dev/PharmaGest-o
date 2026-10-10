# Domain Model — FarmaGestão

Este documento descreve os conceitos fundamentais do domínio do FarmaGestão e seus relacionamentos. Ele responde à pergunta: quais são as coisas importantes que existem neste sistema e como elas se relacionam?

O modelo representa conceitos, não necessariamente as tabelas do banco. As relações seguem o diagrama do banco do grupo. Visão, escopo e perfis de acesso estão em `docs/project-overview.md`.

Quando um atributo é necessário para o sistema mas ainda não existe no banco, ele aparece marcado com "(ainda não existe no banco)".

## Visão geral do domínio

```text
Usuário
  └── Funcionário (gestor ou colaborador)
        └── Pedido (como atendente)

Cliente
  ├── Endereço
  ├── Receita médica
  │     └── Item da receita ── Produto
  └── Pedido
        ├── Item do pedido ── Produto ── Categoria
        │     │                   └───── Fornecedor
        │     └── Item da receita (somente produto controlado)
        └── Venda
              └── Pagamento
```

Uma farmácia vende produtos a clientes. Cada compra é registrada como um pedido, feito por um funcionário e composto por itens. O pedido confirmado vira uma venda, que tem um pagamento. Produtos controlados exigem uma receita do cliente. Quem opera o sistema é um usuário, ligado a um funcionário, com perfil de gestor ou colaborador.

## Usuário

Representa a conta de acesso ao sistema.

### Responsabilidade

Identificar quem entra no sistema e definir o perfil (gestor ou colaborador), que determina o que a pessoa pode ver e fazer.

### Principais informações

- login;
- senha (armazenada com hash);
- perfil de acesso (gestor ou colaborador);
- situação (ativo ou inativo).

### Relacionamentos

Um usuário pertence a um único funcionário. Um funcionário possui um único usuário.

### Regras estruturais

- O login é único.
- Todo usuário tem um perfil de acesso.
- O gestor também é um funcionário, com perfil de gestor.
- Usuário inativo não acessa o sistema.
- O colaborador pode alterar o próprio login e senha. O gestor não tem essa tela.
- Cliente não é usuário e não acessa o sistema.

## Funcionário

Representa uma pessoa da equipe da farmácia, gestor ou colaborador.

### Responsabilidade

Ser o atendente que registra os pedidos e as vendas, e ter seus dados cadastrais mantidos pelo gestor.

### Principais informações

- nome;
- CPF;
- data de nascimento;
- telefone;
- e-mail;
- cargo;
- data de admissão;
- salário (ainda não existe no banco).

### Relacionamentos

Um funcionário possui um usuário de acesso. Um funcionário pode registrar vários pedidos. Cada pedido é registrado por um único funcionário.

### Regras estruturais

- O CPF é único.
- Somente o gestor cadastra, edita e inativa funcionários.
- Ao cadastrar um funcionário, o usuário e a senha de acesso são gerados.
- O salário é visível apenas ao gestor.
- Como o histórico de pedidos guarda quem atendeu, a saída de um funcionário é registrada inativando o usuário.

## Cliente

Representa uma pessoa que compra na farmácia. É um cadastro mantido pela farmácia, sem acesso ao sistema.

### Responsabilidade

Identificar quem comprou, manter o histórico de compras e permitir a venda de medicamentos controlados, que exigem cliente cadastrado.

### Principais informações

- nome;
- CPF;
- data de nascimento;
- telefone;
- e-mail;
- data de cadastro;
- situação (ativo ou inativo; ainda não existe no banco).

### Relacionamentos

Um cliente pode ter vários endereços, vários pedidos e várias receitas médicas.

### Regras estruturais

- O CPF é único.
- O cliente nunca é apagado: é inativado, e o histórico de compras é mantido.
- Cliente inativo não pode ser usado em novos pedidos.
- Um pedido pode não ter cliente cadastrado ("cliente balcão"), exceto quando houver medicamento controlado.
- Colaboradores cadastram, editam e inativam clientes. O gestor apenas consulta.

## Endereço

Representa um endereço de um cliente.

### Responsabilidade

Guardar onde o cliente pode ser encontrado.

### Principais informações

- logradouro;
- número;
- bairro;
- cidade;
- estado;
- CEP;
- complemento;
- tipo.

### Relacionamentos

Um endereço pertence a um único cliente. Um cliente pode ter vários endereços.

### Regras estruturais

- Um endereço não existe sem cliente.
- O endereço do fornecedor é um dado do próprio fornecedor, e não usa este conceito.

## Categoria

Representa um grupo de produtos de mesmo tipo, como analgésico, antibiótico ou ansiolítico.

### Responsabilidade

Organizar os produtos para facilitar consulta e cadastro.

### Principais informações

- nome da categoria.

### Relacionamentos

Uma categoria possui vários produtos. Um produto pertence a uma única categoria.

### Regras estruturais

- Todo produto tem categoria.
- Somente o gestor cadastra, edita e remove categorias.

## Fornecedor

Representa uma empresa que abastece a farmácia.

### Responsabilidade

Manter os dados de contato de quem fornece os produtos e indicar de quem cada produto vem.

### Principais informações

- nome;
- CNPJ;
- telefone;
- e-mail;
- endereço;
- prazo de entrega (ainda não existe no banco).

### Relacionamentos

Um fornecedor fornece vários produtos. Um produto tem um único fornecedor.

### Regras estruturais

- O CNPJ é único.
- Somente o gestor cadastra, edita e remove fornecedores.
- Os pedidos de compra ao fornecedor ficam fora do escopo inicial.

## Produto

Representa um medicamento ou item vendido pela farmácia.

### Responsabilidade

Dizer o que pode ser vendido, por quanto, e quanto há disponível em estoque.

### Principais informações

- nome;
- descrição;
- código de barras;
- categoria;
- fornecedor;
- preço de venda;
- indicação de medicamento controlado;
- quantidade em estoque (ainda não existe no banco);
- estoque mínimo (ainda não existe no banco).

### Relacionamentos

Um produto pertence a uma categoria e a um fornecedor. Um produto pode aparecer em vários itens de pedido e em vários itens de receita.

### Regras estruturais

- Não é possível vender um produto sem estoque nem em quantidade maior que a disponível.
- A quantidade em estoque diminui a cada venda e nunca fica negativa.
- Produto com estoque abaixo do mínimo é sinalizado para reposição.
- Produto controlado só pode ser vendido a cliente cadastrado e com receita informada.
- O preço praticado fica registrado no item do pedido. Alterar o preço do produto não muda vendas já feitas.
- Somente o gestor cadastra, edita e remove produtos. Colaboradores consultam o estoque.
- A quantidade em estoque fica no próprio produto e é reduzida diretamente pela venda. Lotes e movimentação de estoque ficam fora do escopo inicial.

## Pedido

Representa a solicitação de compra: os produtos e as quantidades que um cliente quer levar, registrada por um funcionário.

### Responsabilidade

Reunir os itens de uma compra antes de ela ser confirmada como venda, identificar quem atendeu e validar se há estoque para cada item.

### Principais informações

- cliente (opcional);
- funcionário que atendeu;
- data do pedido;
- status;
- canal, presencial ou online (ainda não existe no banco);
- itens.

Cada **item do pedido** reúne:

- produto;
- quantidade;
- valor unitário;
- item da receita, quando o produto é controlado.

### Relacionamentos

Um pedido pertence a um cliente (quando houver) e é registrado por um funcionário. Um pedido contém um ou mais itens. Cada item se refere a um único produto e, se o produto for controlado, a um item da receita que o autoriza. Um pedido gera, no máximo, uma venda.

### Regras estruturais

- Um pedido tem pelo menos um item, e cada item tem quantidade mínima de 1.
- O mesmo produto aparece uma única vez no pedido: quantidades repetidas são somadas.
- A quantidade de cada item não pode ser maior que o estoque disponível do produto.
- Toda venda identifica o canal e o atendente, que vêm do pedido.
- O atendente é o colaborador que registra o pedido, inclusive quando o canal é online.

## Venda

Representa a compra confirmada e registrada pela farmácia.

### Responsabilidade

Ser o registro oficial do que foi vendido, quando e por quanto. É a base do painel do gestor e dos relatórios de vendas.

### Principais informações

- data da venda;
- valor total;
- status.

Cliente, atendente, canal e itens vendidos vêm do pedido.

### Relacionamentos

Uma venda nasce de um único pedido, e cada pedido tem no máximo uma venda. Uma venda tem um pagamento.

### Regras estruturais

- O valor total corresponde à soma dos itens do pedido.
- Ao registrar a venda, o estoque dos produtos vendidos é reduzido.
- A venda é bloqueada se algum item não tiver estoque suficiente.
- Venda com medicamento controlado exige cliente cadastrado e receita.
- Vendas registradas não são editadas nem removidas pelas telas.
- Colaboradores registram e consultam vendas. O gestor apenas consulta.

## Pagamento

Representa como a venda foi paga.

### Responsabilidade

Registrar a forma de pagamento escolhida ao fechar a venda.

### Principais informações

- forma de pagamento (dinheiro, cartão ou Pix);
- valor.

### Relacionamentos

Um pagamento pertence a uma única venda. Uma venda tem um pagamento.

### Regras estruturais

- Toda venda tem forma de pagamento.
- O valor do pagamento corresponde ao total da venda.
- No escopo inicial não há controle de parcelas, status de pagamento ou conciliação.

## Receita médica

Representa o documento que autoriza a venda de um medicamento controlado.

### Responsabilidade

Garantir a rastreabilidade das vendas de controlados, ligando o medicamento vendido a um cliente e a uma receita.

### Principais informações

- número da receita (ainda não existe no banco);
- cliente;
- nome do médico;
- CRM do médico;
- data de emissão;
- data de validade.

Cada **item da receita** reúne:

- produto prescrito;
- dosagem;
- posologia;
- quantidade prescrita.

### Relacionamentos

Uma receita pertence a um cliente, e um cliente pode ter várias receitas. Uma receita tem itens, e cada item se refere a um produto. O item do pedido de um produto controlado aponta para o item da receita que o autoriza.

### Regras estruturais

- Venda com medicamento controlado exige receita com número informado.
- Ao vender um controlado, registra-se a receita (número e cliente) e, para cada produto controlado, um item da receita mínimo (produto e quantidade), para o qual o item do pedido aponta.
- Médico, CRM, datas de emissão e validade, dosagem e posologia não são exigidos no escopo inicial. Esses campos devem ser opcionais.

## Conceitos fora do escopo inicial

Os conceitos abaixo existem no modelo de dados do grupo, mas não fazem parte do escopo inicial e não são detalhados aqui:

- lote e validade dos produtos;
- pedido de compra aos fornecedores e seus itens;
- movimentação de estoque (histórico completo).

## Regras gerais do domínio

- O gestor administra o cadastro da farmácia (produtos, fornecedores, equipe). O colaborador opera o atendimento (pedidos, vendas e clientes). Os dois consultam o estoque.
- O estoque é consequência das vendas: ele só diminui quando uma venda é registrada e nunca fica negativo.
- Registros ligados ao histórico de vendas, como clientes e usuários de funcionários, não são apagados. São inativados.
- Toda regra de negócio é validada no backend, e o frontend apenas apresenta o resultado.