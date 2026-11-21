## 1. Confirmar contratos e linha de base

- [x] 1.1 Verificar no Xano que cada endpoint de dados usado pelas telas valida token e perfil; se algum endpoint não cumprir o contrato, manter a validação de sessão explícita nesse fluxo e registrar o ajuste necessário antes de prosseguir. Os endpoints usados pelos carregadores declaram `auth = "usuario"` e chamam `Identidade/require_active_role`.
- [x] 1.2 Medir, no mesmo ambiente, chamadas Xano e duração de navegações representativas antes da mudança, sem registrar tokens ou dados pessoais. Na primeira navegação para Clientes, o cabeçalho apareceu em 340 ms e a primeira linha em 2.637 ms; o carregador faz duas chamadas sequenciais (`/sessao` e `/clientes`). A contagem vem do fluxo de código, pois as chamadas ao Xano são server-side.

## 2. Otimizar os carregamentos de tela

- [x] 2.1 Atualizar os carregadores de telas com dados para redirecionar sem chamada quando não houver token e usar a resposta autenticada da própria rota para tratar 401/403; verificar com testes que sessão expirada, falta de permissão e dados atualizados continuam corretos. Os carregadores verificam token antes do Xano e tratam 401/403 nas respostas das rotas protegidas.
- [x] 2.2 Manter a consulta de sessão na tela Minha conta e cobrir com teste que ela continua atualizando os dados da identidade. O carregador continua chamando `/sessao` e o teste verifica o retorno atualizado.
- [x] 2.3 Reutilizar um cliente HTTP durante as chamadas sequenciais de cada carregamento e fechá-lo mesmo quando ocorrer erro; verificar com testes que as chamadas do mesmo carregamento compartilham o cliente e que erros continuam sendo mapeados corretamente. `XanoClient` mantém um único cliente no contexto e fecha-o em saída normal ou excepcional.
- [x] 2.4 Adicionar testes para gestor e colaborador que confirmem a remoção de uma chamada `/sessao` por entrada em telas com dados, sem reduzir as chamadas necessárias para carregar esses dados. Os testes cobrem carregadores de Produtos para ambos os perfis e não chamam sessão.

## 3. Validar o resultado integrado

- [x] 3.1 Executar os testes focados de navegação e cliente Xano, a suíte de testes do projeto e `reflex compile --dry`; corrigir qualquer regressão antes de concluir. Executados: suíte completa com 47 testes aprovada e `reflex compile --dry` aprovado.
- [ ] 3.2 Repetir as mesmas navegações da linha de base e comparar duração e quantidade de chamadas; confirmar dados atualizados ao retornar às telas e que o limite configurado do Xano não é excedido.
