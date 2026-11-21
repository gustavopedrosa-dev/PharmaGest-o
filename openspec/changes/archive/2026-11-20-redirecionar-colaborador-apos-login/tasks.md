## 1. Redirecionamento pós-login

- [x] 1.1 Ajustar o destino após login pelo perfil da sessão e verificar que gestor segue para `/dashboard` e colaborador para `/vendas`.
- [x] 1.2 Adicionar testes de regressão para ambos os perfis, confirmando que o login do colaborador não aciona o fluxo do painel nem mostra falta de permissão.

## 2. Verificação integrada

- [x] 2.1 Executar a suíte de testes e `reflex compile --dry`; confirmar que colaboradores continuam sem acesso direto ao painel do gestor.
