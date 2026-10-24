## 1. Banco e autorização no Xano

- [x] 1.1 Adicionar o campo `ativo` à tabela `cliente` com padrão `true`, preservando clientes existentes, e verificar que a alteração é aditiva no modelo do banco
- [x] 1.2 Criar ou ajustar a função de autorização para exigir sessão válida e distinguir gestor de colaborador, verificando respostas 401 e 403 em chamadas sem permissão
- [x] 1.3 Criar os endpoints de listagem e consulta de clientes, retornando a situação `ativo` e aplicando a autorização definida, verificando seus payloads com dados de teste
- [x] 1.4 Criar os endpoints de cadastro, edição e inativação de clientes, validando CPF único e preservação do histórico, verificando os cenários de sucesso e conflito
- [x] 1.5 Criar os endpoints de cadastro e consulta de endereços vinculados a cliente existente, verificando rejeição de `id_cliente` inexistente e retorno somente dos endereços vinculados
- [x] 1.6 Validar no endpoint de criação de pedido que cliente inativo não pode ser associado a novo pedido, verificando que pedidos históricos continuam consultáveis

## 2. Cliente HTTP e estado Reflex

- [x] 2.1 Adicionar modelos e métodos do `XanoClient` para clientes e endereços, verificando serialização dos campos opcionais e conversão das respostas
- [x] 2.2 Adicionar ao estado Reflex os campos e eventos de consulta, cadastro, edição e inativação de clientes, verificando tratamento de sessão expirada, proibição e indisponibilidade
- [x] 2.3 Adicionar os eventos de cadastro e consulta de endereços na tela de cliente, verificando que o endereço exige um cliente existente

## 3. Interface por perfil

- [x] 3.1 Criar a tela de clientes para consulta por gestor e colaborador, exibindo a situação ativo ou inativo e verificando que ambos conseguem consultar sem expor ações indevidas
- [x] 3.2 Exibir formulário e ações de manutenção somente para colaborador, verificando cadastro, edição, confirmação de inativação e mensagens de validação
- [x] 3.3 Exibir os endereços vinculados ao cliente e o formulário de inclusão para colaborador, verificando atualização da lista após o cadastro

## 4. Testes e verificação integrada

- [x] 4.1 Adicionar testes de contrato do `XanoClient` para listagem, cadastro, edição, inativação, endereços e erros 401/403, verificando a suíte Python existente
- [x] 4.2 Adicionar testes dos cenários críticos de unicidade de CPF, cliente inativo e vínculo de endereço, verificando que nenhum caso altera dados indevidamente
- [x] 4.3 Executar validação OpenSpec e os testes automatizados da change, verificando o fluxo colaborador cadastra cliente -> cadastra endereço -> cliente é consultado pelo gestor -> cliente inativado -> novo pedido é bloqueado