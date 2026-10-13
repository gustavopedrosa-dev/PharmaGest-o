## 1. Pré-condições do Xano

- [x] 1.1 Confirmar que o workspace `Gustavo's Workspace` (`v1`) continua dedicado ao FarmaGestão e não atende usuários finais; baixar um export de segurança sem registros/variáveis de ambiente e verificar que coincide com `xano/` antes de qualquer alteração.
- [x] 1.2 Confirmar que o workspace `v1` suporta execução de função com entradas fornecidas em tempo de execução (`xano function run` com `--data`, JSON ou stdin); não será necessário endpoint temporário apenas para executar o bootstrap. Não passar credenciais reais como argumentos de terminal.

## 2. Autenticação e autorização no Xano

- [x] 2.1 Pela interface do Xano, ativar autenticação em `usuario`, tipar `senha_hash` como `password` obrigatório, tornar `perfil_acesso` enum obrigatório com `gestor`/`colaborador`, tornar `ativo` não anulável com padrão verdadeiro e remover unicidade de senha; validar o schema no workspace `v1`. A verificação funcional de criação e comparação do hash será feita nos testes HTTP da tarefa 4.1, após implementar o login.
- [ ] 2.2 Criar função de bootstrap manual que cria funcionário Gestor e usuário uma única vez; executá-la com dados de teste e verificar vínculo 1:1, recusa de segunda execução e ausência de senha em código, logs e resposta.
- [ ] 2.3 Criar login e consulta da sessão em `usuario`, token de oito horas, autorização por perfil consultada no banco, bloqueio de conta inativa e endpoints para alterar somente o próprio login/senha, exigindo senha atual para troca e mantendo a sessão; criar no ambiente Xano de desenvolvimento da Change (`v1` dedicado nesta configuração) uma rota temporária exclusiva do gestor que use a mesma função de checagem de perfil das rotas reais; verificar por HTTP gestor=200, colaborador=403 e sem token=401.
- [ ] 2.4 Remover a rota temporária de verificação antes de integrar a Change; verificar no Xano e no export que ela não existe.
- [ ] 2.5 Depois de login e autorização novos passarem nos testes HTTP da tarefa 4.1, remover endpoints, addon, funções, `user` e `event_log` do Quick Start pela interface Xano; verificar que não restam referências a essas tabelas/rotas e que signup e endpoints legados não estão disponíveis.

## 3. Integração e experiência Reflex

- [ ] 3.1 Criar `.env.example` sem valores reais, ignorar `.env` no Git e centralizar URL, token e erros em `api/xano.py`; verificar testes do cliente HTTP e que nenhum segredo ou token é exposto ao navegador ou staged.
- [ ] 3.2 Implementar login, logout e estado de sessão server-side, consulta de sessão em páginas protegidas e tratamento HTTP 401/403/4xx/5xx/timeouts; verificar redirecionamentos, as mensagens literais acordadas, e a manutenção/limpeza da sessão por status.
- [ ] 3.3 Implementar navegação por perfil e páginas Minha conta para Gestor e Colaborador; verificar que cada perfil altera apenas o próprio login/senha, exige a senha atual para troca e mantém a sessão após salvar.

## 4. Verificação integrada

- [ ] 4.1 Executar testes de contrato HTTP contra o workspace Xano `v1` para login válido/inválido, conta inativa, token ausente/inválido/expirado, conflito de login e erros 4xx de regra; confirmar que a senha é armazenada como hash e comparada corretamente pelo login; consolidar com os testes 200/403/401 da rota temporária feitos na tarefa 2.3 e confirmar as mensagens do backend. Concluir estes testes antes da remoção prevista na tarefa 2.5.
- [ ] 4.2 Testar o cliente Reflex `api/xano.py` com transporte HTTP mockado para respostas 5xx e timeout; confirmar que ambos mantêm a sessão e mostram "Serviço indisponível, tente novamente" sem chamar o workspace Xano.
- [ ] 4.3 Verificar de ponta a ponta ambos os perfis no Reflex, incluindo bootstrap, login, proteção de rota, navegação, alteração de credenciais e logout; confirmar que nenhum fluxo concede perfil enviado pelo frontend.
- [ ] 4.4 Baixar export final de `v1` sem registros/variáveis de ambiente, comparar com o snapshot inicial e `xano/`, revisar e atualizar os arquivos versionados; confirmar que a rota temporária e referências Quick Start não existem, que não há segredos e validar OpenSpec. Não disponibilizar `v1` a usuários finais.