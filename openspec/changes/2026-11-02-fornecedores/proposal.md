## Why

O gestor ainda não dispõe de telas e APIs para manter fornecedores, e o formulário de produto exige que ele digite o ID do fornecedor. Um catálogo com validação reduz vínculos inválidos e completa a administração prevista no escopo do FarmaGestão.

## What Changes

- Disponibilizar ao gestor consulta, cadastro, edição e remoção de fornecedores.
- Validar CNPJ único e manter nome, CNPJ, telefone, e-mail e endereço.
- Adicionar `prazo_entrega` como campo opcional no Xano, sem alterar registros existentes.
- Permitir selecionar fornecedor cadastrado no formulário de produto, substituindo a digitação do ID.
- Solicitar confirmação antes de remover um fornecedor.
- Recusar a remoção de fornecedores vinculados a produtos, preservando a integridade referencial e exibindo uma mensagem de validação.
- Exigir perfil gestor no backend para as operações de administração de fornecedores.

## Capabilities

### New Capabilities
- `fornecedores`: gestão de fornecedores e seleção segura nos vínculos de produtos.

### Modified Capabilities
- `produtos-estoque`: seleção de fornecedor cadastrado no formulário de produto e validação do vínculo no backend.

## Impact

- **Xano:** APIs autenticadas de consulta e manutenção de fornecedor, verificação de CNPJ e vínculo com produtos; novo campo opcional `prazo_entrega`.
- **Reflex:** lista/formulário de fornecedores para gestor e seleção de fornecedor no formulário de produto.
- **Compatibilidade:** produtos e fornecedores existentes permanecem válidos; nenhuma exclusão de produto ou pedido de compra será introduzida.
- **Fora do escopo:** pedidos de compra, estoque de fornecedores, prazos automatizados e workflows de reposição.