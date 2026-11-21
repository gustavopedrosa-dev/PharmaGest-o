## Why

Após um login válido, o Reflex envia todos os perfis ao painel exclusivo do gestor. O colaborador recebe brevemente uma mensagem de falta de permissão e é redirecionado para Minha conta, em vez de entrar no fluxo de atendimento.

## What Changes

- Direcionar o gestor ao painel e o colaborador à página Minhas vendas (`/vendas`) imediatamente após autenticação bem-sucedida.
- Manter a proteção do painel para acessos diretos de colaboradores.
- Adicionar verificação para os destinos de login de ambos os perfis.

## Capabilities

### New Capabilities

### Modified Capabilities
- `identidade-autorizacao`: definir a página inicial de cada perfil após login válido.

## Impact

- Reflex: ajustar o redirecionamento no evento de login, usando o perfil retornado pela sessão.
- Testes: verificar os destinos após login de gestor e colaborador.
- Xano e banco de dados: sem alterações; a API de login já retorna o perfil do usuário.
