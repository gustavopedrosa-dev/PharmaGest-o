## Why

O sistema já autentica gestores e colaboradores, mas ainda não permite administrar a equipe nem entregar acessos de forma controlada. Esta change fecha o ciclo de gestão de funcionários e disponibiliza ao colaborador a manutenção segura das próprias credenciais.

## What Changes

- Permitir que o gestor consulte, cadastre, edite e inative funcionários.
- Criar ou atualizar, junto com o funcionário, seu usuário de acesso e uma senha inicial protegida por hash.
- Adicionar e proteger o campo de salário, visível somente ao gestor.
- Impedir que funcionário ou usuário inativado acesse o sistema ou seja usado como atendente em novos pedidos.
- Permitir que o colaborador altere o próprio login e senha, exigindo a senha atual para troca de senha.
- Disponibilizar no Reflex as telas de equipe e minha conta conforme o perfil.
- Manter fora do escopo fornecedores, painel gerencial, recuperação de senha e exclusão física de funcionários ou usuários.

## Capabilities

### New Capabilities

- `equipe-minha-conta`: administração de funcionários, provisionamento de acesso e manutenção das próprias credenciais pelo colaborador.

### Modified Capabilities

- `identidade-autorizacao`: restringir a área “Minha conta” ao colaborador e manter as regras de autenticação, sessão e hash coerentes com o provisionamento de usuários da equipe.

## Impact

- **Xano:** tabela `funcionario`, campo aditivo `salario`, tabela `usuario`, endpoints protegidos de equipe e credenciais, além das validações de sessão e atendente ativo.
- **Reflex:** cliente HTTP, estado server-side, navegação por perfil e telas de equipe/minha conta.
- **Pedidos:** validação de funcionário ativo ao registrar novos pedidos, preservando o histórico de atendimentos.
- **Testes:** contratos de API, autorização por perfil, hash de senha, inativação e alteração das próprias credenciais.