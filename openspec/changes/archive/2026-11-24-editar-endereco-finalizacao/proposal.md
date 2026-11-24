# Proposal

## Why

O formulário de edição de clientes não permite consultar ou alterar endereços, embora o domínio permita vários endereços por cliente. A API atual só cadastra e lista endereços, portanto a interface precisa de suporte correspondente no Xano para que as alterações sejam persistidas sem duplicar registros.

## What Changes

- Permitir visualizar e editar os endereços existentes de um cliente e adicionar novos endereços no formulário de edição.
- Criar uma operação PATCH autorizada para atualizar um endereço pertencente ao cliente informado.
- Manter o relacionamento cliente-endereço, os endereços existentes e os demais dados do cliente ao salvar.
- Não incluir remoção de endereços nesta change.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `clientes`: permitir que colaboradores consultem, editem e adicionem múltiplos endereços vinculados a um cliente existente.

## Impact

- Xano: novo endpoint PATCH de endereço, com autorização de colaborador e validação de pertencimento ao cliente.
- Reflex: modal de edição de clientes passa a carregar e editar endereços existentes, além de adicionar endereços.
- Testes: contratos de endpoint de endereço, autorização, pertencimento e integração do cliente com seus endereços.
