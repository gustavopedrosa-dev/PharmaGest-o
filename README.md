# FarmaGestão

O FarmaGestão é um aplicativo web para operação interna de farmácias. Ele centraliza vendas, clientes, produtos, estoque, fornecedores e equipe, separando as ações entre gestor e colaborador.

O projeto foi desenvolvido como trabalho acadêmico para a disciplina de banco de dados de Sistemas de Informação da Impacta. O frontend foi construído em Reflex, em Python, e utiliza o Xano como backend e banco de dados.

## Problema resolvido

O sistema substitui controles dispersos por uma única ferramenta para acompanhar vendas, identificar itens abaixo do estoque mínimo e registrar a equipe responsável pelos atendimentos. Também ajuda a controlar medicamentos controlados, que exigem cliente cadastrado e número de receita.

## Público-alvo

- Gestores de farmácia.
- Colaboradores responsáveis pelo atendimento.
- Pessoas avaliadoras que precisam testar o projeto e seus fluxos.

O cliente da farmácia é apenas um cadastro mantido pela equipe; ele não possui acesso ao aplicativo.

## Acesso ao aplicativo

### Versão publicada

Não há uma URL pública configurada neste repositório. A aplicação deve ser publicada em um serviço de hospedagem compatível com Reflex e conectada ao mesmo workspace Xano configurado no projeto.

Até que o deploy seja realizado, o aplicativo pode ser acessado localmente:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install reflex==0.10.0 httpx==0.28.1
```

Crie um arquivo `.env` na raiz do projeto com a URL da API do Xano:

```text
XANO_BASE_URL=https://seu-workspace.xano.io
```

Inicie o aplicativo em modo de produção:

```powershell
.venv\Scripts\reflex.exe run --env prod --single-port
```

Depois, abra a URL exibida pelo Reflex, normalmente `http://localhost:3000/`.

> Não utilize senhas reais em testes públicos. Solicite ao gestor ou ao responsável pelo ambiente as credenciais autorizadas.

## Perfis de usuários

### Gestor

Pode utilizar:

- Visão geral do painel.
- Consulta de vendas e histórico.
- Consulta de estoque.
- Cadastro, edição e inativação de produtos e categorias.
- Cadastro, edição e inativação de fornecedores.
- Cadastro, edição, inativação e reativação de funcionários.
- Consulta de dados da equipe, incluindo salário.

O gestor não pode registrar vendas.

### Colaborador

Pode utilizar:

- Cadastro, edição e inativação de clientes e seus endereços.
- Consulta de estoque.
- Registro e consulta de vendas.
- Atualização do próprio login e senha em Minha conta.

O colaborador não pode acessar painel do gestor, produtos, fornecedores ou equipe.

### Cliente

O cliente é um registro cadastrado pela farmácia. Não possui login e não acessa o aplicativo.

## Funcionalidades

- Login com validação de usuário, senha e perfil.
- Proteção de páginas e operações por perfil.
- Painel do gestor com vendas, itens vendidos, estoque crítico e funcionários ativos.
- Cadastro e manutenção de produtos e categorias.
- Cadastro e manutenção de fornecedores.
- Cadastro e manutenção de clientes e endereços.
- Cadastro de funcionários com criação da conta de acesso.
- Inativação e reativação de funcionários.
- Registro de vendas presenciais ou online.
- Seleção de forma de pagamento entre dinheiro, cartão e Pix.
- Cálculo automático do valor total da venda.
- Baixa automática do estoque após a confirmação.
- Bloqueio de venda sem estoque suficiente.
- Exigência de cliente e número da receita para medicamentos controlados.
- Histórico de vendas e identificação do atendente.
- Atualização de login e senha pelo colaborador.

## Manual de utilização

### 1. Entrar no sistema

1. Abra a página inicial ou `/login`.
2. Informe o login e a senha fornecidos pelo gestor ou responsável pelo ambiente.
3. Selecione ou aguarde a identificação automática do perfil.
4. Confirme a entrada.

**Resultado esperado:** contas ativas são redirecionadas para a área correspondente ao perfil. Contas inativas ou inválidas não conseguem entrar.

### 2. Utilizar o painel como gestor

1. Entre com uma conta de gestor.
2. Acesse **Visão geral** no menu.
3. Consulte vendas do dia, valor vendido, itens vendidos e estoque abaixo do mínimo.

**Resultado esperado:** os indicadores refletem os dados válidos cadastrados no Xano.

### 3. Cadastrar ou editar um produto

1. Entre como gestor.
2. Acesse **Produtos**.
3. Clique em **Cadastrar** ou **Editar**.
4. Informe nome, descrição, código de barras, categoria, fornecedor, preço, quantidade em estoque e estoque mínimo.
5. Marque **Medicamento controlado** quando o produto exigir receita.
6. Confirme o cadastro ou a edição.

**Resultado esperado:** o produto aparece na lista e passa a estar disponível para consulta e venda. Produtos abaixo do mínimo são destacados como necessidade de reposição.

### 4. Cadastrar um cliente

1. Entre como colaborador.
2. Acesse **Clientes**.
3. Clique em cadastrar.
4. Informe nome, CPF, data de nascimento, telefone, e-mail e endereço.
5. Confirme o cadastro.

**Resultado esperado:** o cliente fica disponível para seleção em vendas e mantém o histórico de compras.

Para editar um cliente, utilize **Editar** na linha correspondente. Para retirar um cliente do uso em novas vendas, utilize a confirmação de inativação. O cadastro não é apagado.

### 5. Cadastrar um funcionário

1. Entre como gestor.
2. Acesse **Equipe**.
3. Clique em cadastrar funcionário.
4. Informe os dados pessoais, cargo e salário.
5. Informe o login desejado e finalize o cadastro.
6. Guarde e entregue ao funcionário a senha inicial exibida no momento do provisionamento.

**Resultado esperado:** funcionário e conta de acesso são criados com o perfil de colaborador e situação ativa.

### 6. Inativar ou reativar um funcionário

1. Entre como gestor.
2. Acesse **Equipe**.
3. Localize o funcionário.
4. Clique em **Inativar** para desativar o acesso ou em **Reativar** para restaurá-lo.
5. Confirme a ação no diálogo.

**Resultado esperado:** a conta inativa deixa de acessar o sistema e não pode registrar novas vendas. Ao reativar, a conta volta a ficar ativa e o perfil de colaborador é preservado. O histórico anterior continua disponível.

### 7. Registrar uma venda

1. Entre como colaborador.
2. Acesse **Atendimento** ou **Novo atendimento**.
3. Informe o código do produto e a quantidade.
4. Clique em **Adicionar item**.
5. Repita a operação para adicionar outros produtos.
6. Confira o nome e a quantidade de cada item.
7. Confira o **Valor total**, calculado automaticamente por quantidade e preço.
8. Informe o ID do cliente, quando necessário.
9. Selecione canal presencial ou online.
10. Selecione dinheiro, cartão ou Pix.
11. Informe o número da receita quando houver produto controlado.
12. Clique em **Confirmar venda**.

**Resultados esperados:**

- Itens são exibidos pelo nome e pela quantidade.
- O valor total é atualizado ao adicionar os produtos.
- O estoque dos produtos é reduzido após a confirmação.
- A venda não é salva sem estoque suficiente.
- Produto controlado exige cliente cadastrado e número da receita.
- O histórico registra canal, atendente, forma de pagamento e itens.

Se alguma regra impedir a venda, uma mensagem vermelha de erro aparece no modal informando o motivo.

### 8. Consultar vendas e estoque

**Colaborador:**

1. Acesse **Vendas** para consultar o histórico disponível.
2. Acesse **Estoque** para consultar disponibilidade e produtos abaixo do mínimo.

**Gestor:**

1. Acesse **Vendas** para consultar o histórico.
2. Acesse **Estoque** para acompanhar reposição.
3. Acesse o painel para acompanhar indicadores do dia.

### 9. Alterar login e senha

Somente colaboradores podem alterar suas próprias credenciais.

1. Acesse **Minha conta**.
2. Informe o novo login e confirme.
3. Para alterar a senha, informe a senha atual e a nova senha nos campos correspondentes.
4. Confirme a operação.

**Resultado esperado:** o colaborador continua na sessão atual com o mesmo perfil e vínculo com o funcionário. Senhas inválidas ou usadas por outra conta são recusadas.

## Exemplos de utilização

### Venda comum

Exemplo de cenário:

- Produto: Dipirona.
- Quantidade: 2.
- Preço unitário: R$ 12,50.
- Canal: presencial.
- Forma de pagamento: dinheiro.

Ao adicionar o item, a área de itens mostra **Dipirona - Quantidade: 2** e o total mostrado é **R$ 25,00**. Após confirmar, o estoque diminui duas unidades.

### Venda de medicamento controlado

Exemplo de cenário:

- Cliente cadastrado e ativo.
- Medicamento marcado como controlado.
- Número da receita informado.

O sistema permite confirmar a venda e registra o vínculo com o cliente e a receita.

Se o número da receita estiver vazio, o sistema informa:

> Venda de medicamento controlado não pode ser realizada sem número da receita.

### Reposição de estoque

Se um produto tiver quantidade menor que o estoque mínimo, ele aparece destacado como necessidade de reposição. O usuário não consegue vender quantidade superior à disponível.

### Inativação e reativação

Ao inativar um funcionário, a conta não pode fazer novo login. Ao reativar, o usuário volta a poder entrar com o mesmo perfil e login. Vendas históricas permanecem vinculadas ao atendente original.

## Capturas de tela

O repositório não versiona atualmente um conjunto completo de capturas de tela. Recomenda-se adicionar imagens em `docs/screenshots/` ao publicar o sistema, por exemplo:

- Tela de login.
- Painel do gestor.
- Cadastro de produto.
- Cadastro de cliente.
- Novo atendimento.
- Confirmação de venda.
- Inativação e reativação de funcionário.

## Limitações conhecidas

- Não há URL pública configurada no repositório; o deploy precisa ser realizado separadamente.
- Não há lote, validade, pedido de compra ou histórico detalhado de movimentação de estoque.
- Não há cadastro detalhado de receita médica. Na venda controlada, somente cliente e número da receita são exigidos.
- Não há controle de parcelas ou conciliação financeira.
- Vendas confirmadas não são editadas ou removidas pela interface para preservar o histórico.
- Funcionários e clientes são inativados em vez de apagados.
- O gestor não registra vendas nem altera cadastros de clientes.
- O colaborador não visualiza salários nem administra equipe, produtos e fornecedores.
- O cliente final não possui conta de acesso.
- A disponibilidade depende da configuração correta de `XANO_BASE_URL` e do workspace Xano associado.

## Tecnologias

- Python e Reflex.
- XanoScript e Xano como backend e banco de dados.
- HTTPX para comunicação entre frontend e backend.
- OpenSpec para especificação das mudanças.

## Estrutura principal

```text
api/                   Adaptador das APIs do Xano
connectdrogs/          Aplicação Reflex
docs/                  Documentação e protótipo
openspec/              Especificações e histórico de changes
tests/                 Testes automatizados
xano/                  Definições XanoScript versionadas
```

## Documentação relacionada

- [Visão do projeto](docs/project-overview.md)
- [Modelo de domínio](docs/domain-model.md)
- [Especificação da equipe](openspec/specs/equipe-minha-conta/spec.md)
- [Especificação de vendas](openspec/specs/vendas/spec.md)
