## Why

O projeto ainda usa a autenticação genérica do Quick Start, separada da tabela `usuario` do domínio, e não aplica os perfis Gestor e Colaborador nas APIs. É necessário estabelecer uma identidade única ligada ao funcionário e entregar login, sessão e autorização confiáveis antes dos fluxos operacionais.

## What Changes

- Ativar autenticação na tabela `usuario`, usar o tipo `password` para a credencial e restringir os perfis a `gestor` e `colaborador`.
- Criar o primeiro gestor por bootstrap manual, executável uma única vez no Xano e sem endpoint público.
- Implementar login, token com validade de oito horas, consulta da sessão e bloqueio de usuários inativos, com mensagens de autenticação genéricas.
- Aplicar autorização por perfil no backend, consultando perfil e situação ativa no banco; disponibilizar navegação e páginas Reflex conforme o perfil.
- Oferecer a ambos os perfis uma área Minha conta para alterar login e senha; a troca de senha exige a senha atual e mantém a sessão ativa.
- Centralizar chamadas Reflex ao Xano em `api/xano.py`, configurar `XANO_BASE_URL` e tratar respostas HTTP e indisponibilidade conforme o contrato definido.
- Remover as tabelas `user` e `event_log` e os componentes Quick Start que dependem delas, incluindo cadastro público e endpoints auxiliares de autenticação, logs e e-mail.
- Testar por HTTP os códigos e mensagens para autenticação inválida/expirada, falta de permissão, erros de regra, indisponibilidade e timeout.

Ficam fora do escopo: cadastro e gestão de funcionários, clientes, produtos e fornecedores; salário; estoque; vendas; receitas; recuperação por e-mail; refresh token; e qualquer credencial administrativa no Reflex. Funcionários criados futuramente pela tela Equipe devem receber perfil Colaborador, definido pelo backend e nunca pelo frontend.

## Capabilities

### New Capabilities
- `identidade-autorizacao`: autenticação, sessão, bootstrap inicial, autorização por perfil e gestão das credenciais próprias para Gestor e Colaborador.

### Modified Capabilities
- Nenhuma. Ainda não existem specs principais em `openspec/specs/`.

## Impact

- Xano: tabela `usuario`, autenticação, funções de bootstrap e autorização, APIs de login/sessão/conta, remoção dos artefatos Quick Start baseados em `user` e grupos de API.
- Reflex: módulo cliente `api/xano.py`, configuração de ambiente, fluxo de login, proteção de páginas, sessão server-side, tratamento de erros, menus por perfil e páginas Minha conta.
- Configuração local: `.env.example` sem valores secretos; `.env` local ignorado pelo Git.
- Operação: o workspace dedicado usa `v1` como desenvolvimento desta Change, sem branch pago e com aplicação manual pela interface Xano; exports antes/depois serão comparados antes de atualizar os arquivos versionados. `v1` não será usado como produção.