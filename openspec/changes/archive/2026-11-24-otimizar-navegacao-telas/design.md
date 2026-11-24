## Context

Consulte [proposal.md](./proposal.md) para a motivação. Hoje, os carregadores de telas chamam `load_session` antes de buscar dados. Essas chamadas de dados já enviam o token e tratam 401/403; o Xano é a autoridade de autenticação e autorização. O cliente HTTP também cria um `httpx.Client` novo para cada requisição, inclusive quando um carregador faz várias leituras sequenciais.

## Goals / Non-Goals

**Goals:**
- Remover a chamada `/sessao` redundante nas telas cuja chamada protegida de dados valida token e perfil.
- Manter os dados atualizados a cada entrada na tela e preservar o tratamento de erros e redirecionamentos.
- Reutilizar a conexão HTTP dentro de cada carregamento que faça várias chamadas sequenciais.
- Reduzir chamadas por entrada em uma nas telas com carregamento de dados, sem disparar chamadas paralelas que possam criar picos no limite do Xano.

**Non-Goals:**
- Alterar endpoints, regras de negócio, permissões ou estrutura de dados no Xano.
- Guardar dados das telas em cache entre navegações.
- Alterar a frequência de consulta de sessão na tela Minha conta, que precisa carregar a identidade atual.
- Assumir ou alterar o limite de requisições do plano Xano; ele deve ser confirmado separadamente.

## Decisions

1. **Usar a chamada de dados protegida como validação da navegação.** Antes de remover `load_session` de um carregador, confirmar que todas as rotas Xano chamadas por ele validam token e perfil. Manter a verificação local de token ausente para encaminhar ao login sem gerar uma chamada. Continuar tratando 401 como sessão expirada e 403 como falta de permissão. Se uma rota não cumprir o contrato de autorização, não remover a validação de sessão desse fluxo.

2. **Manter o carregamento de dados em cada entrada.** Não usar cache de listas ou resumos: isso preserva a atualização dos dados depois de alterações em vendas, produtos, clientes e demais cadastros.

3. **Usar um cliente HTTP com escopo de carregamento.** Cada carregador cria um cliente Xano e o mantém aberto durante suas leituras sequenciais; o cliente usa um único `httpx.Client` nesse escopo e fecha a conexão ao terminar. Isso permite keep-alive sem um singleton global nem ciclo de vida compartilhado entre sessões Reflex.

4. **Manter chamadas sequenciais.** Paralelizar leituras não reduz a quantidade de requisições e pode concentrá-las em uma janela curta do limite do Xano. A redução de latência deve vir da remoção da consulta de sessão duplicada e do reaproveitamento da conexão.

5. **Verificar redução por contagem e por tempo.** Testes com transportes simulados devem provar o número de chamadas por carregador e preservar os casos 401/403. A validação manual deve comparar a navegação antes/depois no mesmo ambiente e registrar a quantidade de chamadas e o tempo observado; não declarar um ganho em milissegundos sem essa medição.

## Risks / Trade-offs

- [Perfil ou nome alterado fora desta sessão pode permanecer no estado Reflex até uma consulta de sessão] → O backend continua validando a autorização em cada endpoint protegido; manter a consulta na tela Minha conta e cobrir a atualização de sessão por seus fluxos existentes.
- [Algum endpoint Xano pode não validar o perfil como esperado] → Inspecionar e testar as rotas usadas por cada carregador antes de retirar sua consulta de sessão; não relaxar autorização no frontend como substituto.
- [A taxa de requisições permitida pode depender do plano ou configuração Xano] → Registrar o limite real no ambiente de validação; a mudança reduz uma chamada por navegação de tela com dados, mas não presume o valor do limite.
- [A conexão pode não ser reutilizada se o cliente for fechado entre chamadas] → Testar o escopo do cliente e garantir seu fechamento após cada carregamento, inclusive em caso de erro.

## Migration Plan

Não há migração de dados nem mudança de endpoint. Publicar apenas as alterações do Reflex e do adaptador HTTP; em caso de regressão de autorização ou navegação, reverter essas alterações e manter o carregamento anterior com consulta explícita de sessão.

## Open Questions

- Confirmar no ambiente Xano usado pelo projeto o limite efetivo de requisições e comparar os tempos observados antes e depois; isso não altera o desenho, mas contextualiza o ganho real.
