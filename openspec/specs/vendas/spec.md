# vendas Specification

## Purpose

Definir o atendimento, a confirmação de vendas e os registros de pagamento do FarmaGestão, garantindo rastreabilidade do atendente, integridade do estoque e controle adicional para medicamentos controlados.

## Requirements

### Requirement: Colaborador registra pedido de venda
O sistema SHALL permitir que um colaborador autenticado registre um pedido com um ou mais produtos, quantidades positivas, canal presencial ou online e atendente identificado pela sessão, sem permitir que dados de autorização sejam definidos pelo frontend.

#### Scenario: Colaborador cria pedido válido
- **WHEN** um colaborador informa itens ativos com quantidades positivas e um canal permitido
- **THEN** o sistema cria um pedido pendente vinculado ao funcionário da sessão e preserva o preço vigente de cada produto no item

#### Scenario: Pedido rejeita item inválido
- **WHEN** um colaborador informa produto inativo, quantidade menor que um ou repete o mesmo produto no pedido
- **THEN** a API recusa o pedido com erro de validação e não cria registros parciais

#### Scenario: Gestor tenta registrar pedido
- **WHEN** um gestor tenta criar ou confirmar um pedido pela API de atendimento
- **THEN** a API recusa a operação com HTTP 403 e não altera dados

### Requirement: Venda confirma pedido e baixa estoque
O sistema SHALL permitir a confirmação de um pedido pendente com forma de pagamento válida, criando uma venda e um pagamento e reduzindo o estoque de todos os itens em uma única operação transacional.

#### Scenario: Colaborador confirma venda dentro do estoque
- **WHEN** um colaborador confirma um pedido pendente com pagamento em dinheiro, cartão ou Pix e todos os itens têm estoque suficiente
- **THEN** o sistema cria uma venda concluída, cria o pagamento com valor igual ao total, reduz todos os estoques e marca o pedido como confirmado

#### Scenario: Estoque insuficiente cancela confirmação
- **WHEN** qualquer item do pedido tem estoque menor que a quantidade solicitada
- **THEN** a API recusa a confirmação e mantém inalterados o pedido, a venda, o pagamento e todos os estoques

#### Scenario: Confirmação repetida é recusada
- **WHEN** um colaborador tenta confirmar novamente um pedido já confirmado ou cancelado
- **THEN** a API recusa a operação e não cria outra venda nem outro pagamento

#### Scenario: Dois atendimentos disputam o último estoque
- **WHEN** confirmações concorrentes tentam vender uma quantidade que não pode ser atendida simultaneamente
- **THEN** no máximo uma confirmação é aceita e o estoque nunca fica negativo

### Requirement: Venda de controlado exige cliente e receita
O sistema SHALL exigir cliente ativo e número de receita para confirmar qualquer pedido que contenha produto controlado, registrando a receita e um item de receita para cada produto controlado vendido.

#### Scenario: Controlado vendido com cliente e receita
- **WHEN** um colaborador confirma pedido com controlado, cliente ativo e número de receita informado
- **THEN** a venda é aceita e a receita fica vinculada ao cliente e aos itens de receita correspondentes aos produtos controlados

#### Scenario: Controlado sem cliente ou receita
- **WHEN** um pedido com produto controlado não informa cliente ativo ou número de receita
- **THEN** a API recusa a confirmação e mantém o estoque e o pedido inalterados

#### Scenario: Cliente balcão compra produto comum
- **WHEN** um colaborador confirma pedido sem controlado e sem cliente identificado
- **THEN** a venda é aceita se as demais regras forem atendidas

### Requirement: Usuários consultam histórico de vendas conforme o perfil
O sistema SHALL permitir que colaboradores consultem as vendas que registraram e que gestores consultem o histórico autorizado da farmácia, sem permitir edição ou remoção de vendas, itens, pagamentos ou receitas.

#### Scenario: Colaborador consulta suas vendas
- **WHEN** um colaborador acessa a consulta de vendas
- **THEN** o sistema retorna as vendas registradas por ele com itens, total, canal e forma de pagamento

#### Scenario: Gestor consulta vendas da farmácia
- **WHEN** um gestor acessa a consulta de vendas
- **THEN** o sistema retorna as vendas autorizadas da farmácia com atendente, itens, total, canal e pagamento

#### Scenario: Usuário tenta alterar venda registrada
- **WHEN** um usuário tenta editar ou excluir uma venda, item, pagamento ou receita registrada
- **THEN** a API recusa a operação e preserva o histórico

#### Scenario: Usuário sem sessão consulta vendas
- **WHEN** uma chamada de consulta de vendas é feita sem token válido
- **THEN** a API responde HTTP 401 e não retorna dados
