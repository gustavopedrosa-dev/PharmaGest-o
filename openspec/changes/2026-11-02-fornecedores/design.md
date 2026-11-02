## Context

Ver proposal.md para motivação e specs para o contrato observável. A tabela `fornecedor` já existe no Xano, tem índice único de CNPJ e é referenciada por `produto.id_fornecedor`; ainda não há APIs ou telas de gestão. O formulário de produto recebe o ID do fornecedor como texto, e o backend já valida que o fornecedor existe.

## Goals / Non-Goals

**Goals:**

- Disponibilizar gestão de fornecedores exclusivamente ao gestor.
- Permitir seleção de fornecedor cadastrado no formulário de produto.
- Acrescentar prazo de entrega sem invalidar fornecedores existentes.
- Preservar a integridade dos produtos que referenciam fornecedores.

**Non-Goals:**

- Não implementar pedidos de compra, estoque de fornecedores ou reposição automatizada.
- Não criar um ciclo de inativação para fornecedores nesta change.
- Não alterar a consulta de estoque dos colaboradores nem os dados de vendas.

## Decisions

### Reutilizar o grupo Xano Produtos

As APIs de fornecedor ficam no grupo `Produtos` existente, com os mesmos guards de perfil gestor usados na administração de produtos. Isso evita um novo grupo/canonical e mantém fornecedor junto ao fluxo que consome seu vínculo. Alternativa considerada: criar um grupo Xano independente; foi rejeitada porque adiciona configuração e canonical sem necessidade funcional.

### Tornar prazo de entrega opcional e aditivo

Adicionar `prazo_entrega` como texto nullable na tabela existente, sem valor padrão. Fornecedores já cadastrados continuam válidos; a API aceita ausência do campo e preserva o texto quando informado. Não há conversão de unidade ou cálculo de data nesta change.

### Remover somente fornecedores sem produtos vinculados

O Reflex solicita confirmação antes de chamar a API. Antes da exclusão, a API verifica produtos associados. Se houver vínculo, responde com erro de regra e preserva fornecedor e produtos; se não houver, remove o fornecedor. Alternativa considerada: inativar; foi adiada porque a tabela e o domínio não possuem campo de situação para fornecedor e a change não deve inventar uma política de reativação.

### Selecionar pelo catálogo no formulário de produto

O formulário de gestor carrega fornecedores pela API e apresenta opções com nome e CNPJ, enviando o ID selecionado no contrato existente de produto. A validação backend de fornecedor existente continua sendo a autoridade; a lista da interface não concede autorização.

### Validar unicidade de CNPJ

A API consulta conflito antes de criar ou atualizar e mantém o índice único atual como proteção de concorrência. Na edição, o próprio fornecedor é excluído da verificação de duplicidade.

## Risks / Trade-offs

- **Fornecedor referenciado não pode ser removido** → mostrar mensagem clara para o gestor reassociar os produtos antes da remoção.
- **Prazo legado ausente** → tratar valor nulo como não informado na lista e no formulário.
- **Falha de carregamento do catálogo** → manter a mensagem do backend visível e impedir salvar produto sem fornecedor válido.
- **CNPJ duplicado por concorrência** → manter o índice único no banco e mapear a violação para mensagem de validação.

## Migration Plan

1. Adicionar a coluna opcional `prazo_entrega` à tabela existente e publicar as APIs de fornecedor no Xano.
2. Validar autorização, CNPJ único, proteção de exclusão vinculada e leitura do catálogo.
3. Integrar telas de fornecedor e seleção no formulário de produto no Reflex.
4. Verificar os fluxos de gestor e colaborador e compilar a aplicação.
5. Em rollback, remover as novas APIs e telas; manter a coluna opcional para não afetar registros já criados.