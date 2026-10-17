## Why

O FarmaGestão já possui a identidade e autorização necessárias, mas ainda não oferece o cadastro de produtos nem o controle operacional do estoque. Sem essa base, o sistema não consegue sinalizar reposição nem impedir vendas acima da quantidade disponível, comprometendo o fluxo principal da farmácia.

## What Changes

- Criar o cadastro de produtos e categorias para o gestor.
- Permitir definir preço, código de barras, fornecedor, indicação de controlado, quantidade em estoque e estoque mínimo.
- Permitir que gestor consulte, crie, edite e inative produtos e categorias conforme as regras do domínio.
- Permitir que gestor e colaborador consultem o estoque sem expor operações administrativas ao colaborador.
- Sinalizar produtos cuja quantidade esteja abaixo do estoque mínimo.
- Aplicar no backend validações de estoque não negativo, quantidade inicial válida e permissões por perfil.
- Criar telas Reflex para listagem, cadastro, edição e consulta de produtos e estoque.
- Manter fora do escopo lotes, validade, pedidos de compra e movimentação histórica de estoque.

## Capabilities

### New Capabilities

- `produtos-estoque`: cadastro, manutenção, consulta e regras de estoque dos produtos e categorias.

### Modified Capabilities

- Nenhuma.

## Impact

- **Xano:** schema da tabela `produto`, validação de campos, endpoints protegidos para produtos/categorias e consultas de estoque.
- **Reflex:** novas páginas de produtos, categorias e estoque, com navegação condicionada ao perfil.
- **Autorização:** gestor administra produtos e categorias; gestor e colaborador consultam estoque.
- **Banco:** alterações aditivas na tabela `produto`; a quantidade em estoque e o estoque mínimo ficam no próprio produto, sem criar tabelas fora do escopo.
- **Dependências futuras:** vendas usarão a quantidade disponível e as regras de estoque desta Change.
