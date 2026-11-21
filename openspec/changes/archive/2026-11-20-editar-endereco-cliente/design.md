## Context

O modelo representa endereço como entidade separada e permite vários registros por cliente. O Xano já expõe GET e POST aninhados ao cliente; o POST exige cidade e estado e permite logradouro, número, bairro, CEP e complemento opcionais. Não há migração de tabela necessária. Ver proposal.md e specs/clientes/spec.md.

## Goals / Non-Goals

**Goals:**

- Atualizar um endereço existente sem mudar seu ID ou cliente associado.
- Carregar e editar vários endereços no modal do cliente, permitindo adicionar novos registros.
- Garantir autorização e pertencimento do endereço no Xano.

**Non-Goals:**

- Remover endereços.
- Alterar o schema de banco ou acrescentar tipo de endereço.
- Mudar os dados cadastrais do cliente além do fluxo já existente.

## Decisions

- Adicionar PATCH aninhado em `/clientes/cliente/{cliente_id}/endereco/{endereco_id}`. A API exige sessão de colaborador, verifica a existência do cliente e confirma que o endereço pertence a ele antes de editar. O endpoint recebe os mesmos campos do POST atual e retorna o endereço atualizado. Essa validação no backend evita depender do ID enviado pela interface.
- Manter o POST existente para novos endereços e o GET para carregar todos os endereços. Cidade e estado permanecem obrigatórios; os demais campos seguem as regras do endpoint atual.
- Usar estado separado para os endereços do modal, preservando o ID dos registros existentes. Linhas sem ID representam novos endereços; uma ação adiciona uma linha em branco. Isso evita sobrescrever estado de endereços usado em outros contextos.
- No salvamento, atualizar o cliente pelo fluxo existente e, em seguida, processar cada endereço: PATCH para registros com ID e POST para linhas novas. Após cada POST bem-sucedido, guardar o ID retornado no estado local para que uma repetição não duplique o endereço. Em erro, manter o modal aberto e apresentar a mensagem retornada.
- Não criar transação agregada para vários endereços, pois as APIs atuais são operações independentes. Cada escrita retorna seu resultado e mantém sua identidade; se uma operação posterior falhar, alterações anteriores permanecem salvas e podem ser reenviadas com os IDs corretos.

## Risks / Trade-offs

- [Uma falha durante o salvamento de vários endereços pode ocorrer após atualizações anteriores] → Persistir IDs retornados após cada POST, manter o formulário e permitir nova tentativa sem duplicar registros.
- [Uma chamada direta com endereço de outro cliente poderia alterar dados alheios] → O PATCH valida no Xano que o endereço selecionado pertence ao cliente informado e exige perfil de colaborador.

## Migration Plan

1. Publicar o novo endpoint PATCH no Xano; nenhuma migração de banco é necessária.
2. Atualizar o cliente Reflex para listar, editar e adicionar endereços.
3. Verificar os fluxos de autorização, propriedade, atualização e adição.
4. Em rollback, remover o uso do PATCH e os controles de endereço do formulário; os registros e a estrutura atuais permanecem compatíveis.
