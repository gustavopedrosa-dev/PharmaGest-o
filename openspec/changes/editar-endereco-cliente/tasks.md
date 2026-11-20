## 1. API de endereços

- [x] 1.1 Criar o endpoint Xano PATCH para atualizar endereço com autorização de colaborador, validação do cliente e vínculo do endereço; verificar cenários de sucesso, cliente inexistente, vínculo incorreto e perfil sem permissão.
- [x] 1.2 Adicionar `XanoClient.update_address` e testes de contrato para método, rota, payload e conversão da resposta; executar os testes de contrato de clientes.

## 2. Formulário de clientes

- [x] 2.1 Carregar todos os endereços ao abrir a edição do cliente e preencher uma lista editável mantendo os IDs; verificar cliente sem endereços e cliente com múltiplos endereços.
- [x] 2.2 Adicionar linhas de endereço no formulário e validar cidade e estado obrigatórias antes do envio; verificar que os demais campos opcionais podem ficar vazios.
- [x] 2.3 Salvar endereço existente via PATCH e endereço novo via POST, guardando cada ID retornado para evitar duplicação em nova tentativa; verificar mensagem e modal aberto em falha parcial.
- [x] 2.4 Renderizar os campos estruturados e ações para múltiplos endereços no modal, sem controle de remoção; compilar e validar o fluxo visual de edição.

## 3. Verificação integrada

- [x] 3.1 Executar os testes de contrato e compilação Reflex; verificar edição de vários endereços, inclusão adicional, autorização e preservação do vínculo cliente-endereço.
