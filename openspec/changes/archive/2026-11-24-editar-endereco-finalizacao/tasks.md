## 1. Endereços no Xano

- [x] 1.1 Criar endpoint PATCH de endereço vinculado ao cliente e validar autorização de colaborador.
- [x] 1.2 Validar que o endereço pertence ao cliente informado.

## 2. Endereços no Reflex

- [x] 2.1 Carregar os endereços existentes ao abrir a edição de cliente.
- [x] 2.2 Permitir adicionar novos endereços e editar os campos dos endereços existentes.
- [x] 2.3 Persistir endereços existentes por PATCH e novos endereços por POST.
- [x] 2.4 Preservar identificadores criados ao ocorrer falha parcial e permitir retry.

## 3. Verificação

- [x] 3.1 Executar testes focados da change.
- [x] 3.2 Executar a suíte completa e `reflex compile --dry`.
