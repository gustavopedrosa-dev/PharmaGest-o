## Context

Consulte `proposal.md` e `specs/identidade-autorizacao/spec.md`. O evento de login atualiza a sessão no estado Reflex e envia todos os perfis para `/dashboard`. O carregamento do painel valida que o perfil seja `gestor`; para colaboradores, exibe falta de permissão e redireciona para `/minha-conta`.

## Goals / Non-Goals

**Goals:**

- Escolher o destino após login pelo perfil já armazenado na sessão autenticada.
- Preservar a autorização do painel e os demais redirecionamentos de sessão.

**Non-Goals:**

- Alterar as permissões no backend ou o comportamento de acesso direto ao painel.
- Mudar a página inicial dos gestores ou outros destinos de navegação.

## Decisions

- Redirecionar `gestor` para `/dashboard` e `colaborador` para `/vendas` no evento de login, após atualizar a sessão. O perfil é fornecido pela sessão validada pelo Xano.
- Manter o bloqueio em `/dashboard`: a seleção de destino melhora o fluxo normal sem enfraquecer a proteção contra acesso direto de colaboradores.
- Usar `/vendas` para colaboradores, conforme preferência definida para esta mudança. `/minha-conta` foi considerada, mas não é a área de operação principal.
- Cobrir ambos os perfis em teste de regressão, verificando que colaborador não passe pelo carregamento do painel.

## Risks / Trade-offs

- [O perfil retornado pela sessão pode divergir do perfil esperado] → Continuar usando a sessão validada pelo backend e manter as verificações de perfil existentes nas páginas e APIs.
