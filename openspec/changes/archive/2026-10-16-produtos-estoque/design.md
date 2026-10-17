## Context

O schema atual de `produto` já possui categoria, fornecedor, identificação, indicação de controlado e preço, mas ainda não possui quantidade em estoque, estoque mínimo ou estado de inativação. A autorização de identidade já consulta o perfil no backend e deve ser reutilizada nas novas APIs. Consulte `proposal.md` e `specs/produtos-estoque/spec.md` para motivação e comportamento.

## Goals / Non-Goals

**Goals:**

- Adicionar ao produto apenas os campos necessários para estoque e disponibilidade.
- Expor APIs protegidas para administração e consulta, com autorização por perfil no backend.
- Manter a baixa de estoque transacional e impedir valores negativos.
- Entregar telas Reflex coerentes com as permissões de gestor e colaborador.
- Preparar contratos reutilizáveis pela futura Change de vendas.

**Non-Goals:**

- Não criar lotes, validade, movimentação histórica ou pedidos de compra.
- Não implementar a venda completa nesta Change.
- Não alterar o modelo de autenticação ou criar um terceiro perfil.
- Não permitir que o frontend seja a fonte de verdade para estoque ou permissões.

## Decisions

- **Estoque no registro de produto:** adicionar `quantidade_estoque`, `estoque_minimo` e um estado de disponibilidade/inativação no próprio produto, em vez de criar uma tabela de movimentações. Isso segue o modelo de domínio e mantém a Change compatível com o escopo inicial.
- **Validação no Xano:** concentrar autorização, validação de valores não negativos e regras de atualização em endpoints/funções Xano. O Reflex apenas envia dados e apresenta erros.
- **Operações separadas por permissão:** usar endpoints de administração para gestor e endpoints de consulta para ambos os perfis. A interface pode ocultar ações do colaborador, mas a API também recusará chamadas indevidas.
- **Inativação em vez de exclusão física:** preservar produtos referenciados por pedidos e histórico, marcando-os como inativos e excluindo-os das novas vendas e consultas operacionais.
- **Baixa protegida para integração futura:** preparar uma função de domínio transacional que valide estoque atual antes de reduzir a quantidade, para que a futura API de vendas não replique a regra.
- **Cliente Reflex centralizado:** adicionar métodos ao cliente Xano existente e manter o token exclusivamente no estado server-side, reaproveitando o tratamento atual de 401, 403, 4xx, 5xx e timeout.

## Risks / Trade-offs

- **[Risco] Concorrência entre vendas simultâneas pode causar baixa incorreta** → executar a leitura e atualização do estoque na mesma transação/rotina do backend e testar duas tentativas concorrentes na verificação.
- **[Risco] Produtos existentes não possuem os novos campos** → usar campos opcionais ou valores padrão aditivos durante a migração e normalizar a resposta da API sem apagar dados existentes.
- **[Risco] Inativação pode quebrar referências históricas** → não excluir fisicamente e manter o produto consultável em históricos autorizados.
- **[Trade-off] Sem histórico de movimentação** → o estoque fica simples e compatível com o escopo, mas auditoria detalhada ficará para uma Change futura se for aprovada.
