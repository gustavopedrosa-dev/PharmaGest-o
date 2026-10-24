## Why

O sistema ainda não possui o cadastro de clientes necessário para identificar compradores, preservar seu histórico e permitir vendas de medicamentos controlados. Esta change entrega essa base antes da evolução dos fluxos de vendas que dependem de um cliente ativo.

## What Changes

- Criar no Xano as operações de consulta, cadastro, edição e inativação de clientes.
- Criar no Xano as operações de cadastro e consulta de endereços vinculados a clientes.
- Aplicar autorização por perfil: colaboradores administram clientes; gestores apenas consultam.
- Impedir o uso de clientes inativos em novos pedidos, mantendo seus registros históricos.
- Adicionar o campo aditivo `cliente.ativo`, com valor padrão ativo.
- Criar no Reflex as telas e formulários correspondentes, com tratamento de erros da API.
- Adicionar testes dos contratos da API, das permissões e da inativação.
- Manter fora do escopo a edição de vendas existentes, o acesso do cliente ao sistema e alterações no cadastro de funcionários ou fornecedores.

## Capabilities

### New Capabilities

- `clientes`: cadastro, consulta, manutenção de situação e endereços de clientes conforme o perfil de acesso.

### Modified Capabilities

- Nenhuma.

## Impact

- **Xano:** tabela `cliente`, tabela `endereco`, endpoints e funções de autorização para operações de clientes.
- **Reflex:** estado server-side, cliente HTTP e telas de clientes integradas à sessão existente.
- **Testes:** novos testes de contrato do cliente Xano e dos fluxos críticos de permissão e inativação.
- **Integração:** vendas futuras poderão consultar clientes ativos sem alterar o histórico de pedidos já registrado.