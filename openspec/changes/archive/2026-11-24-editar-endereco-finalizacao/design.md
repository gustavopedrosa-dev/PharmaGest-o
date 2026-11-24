# Design

## Context

A capacidade de clientes já possui cadastro, consulta e inativação. Os endereços são registros relacionados ao cliente e podem ser múltiplos. Antes desta change, o frontend somente cadastrava o cliente e não oferecia edição completa dos endereços existentes.

## Goals / Non-Goals

**Goals**

- Permitir que o colaborador visualize, edite e adicione endereços na edição de cliente.
- Persistir endereços existentes por PATCH e novos endereços por POST.
- Validar pertença do endereço ao cliente e autorização no backend.

**Non-Goals**

- Remoção de endereços.
- Alteração do vínculo de cliente em endereços existentes.

## Decisions

1. Usar o identificador do endereço para diferenciar registro existente de novo registro.
2. Executar PATCH para `id != ""` e POST para `id == ""`.
3. Validar cidade e estado obrigatórios no frontend e no backend.
4. Preservar dados já criados quando uma operação posterior falhar parcialmente.

## Risks / Trade-offs

- Falha parcial em salvar vários endereços pode deixar parte persistida e outra não. A interface preserva o identificador dos registros já criados para permitir retry seguro.
