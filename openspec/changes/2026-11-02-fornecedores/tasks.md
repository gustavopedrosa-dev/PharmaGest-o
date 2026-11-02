## 1. Dados e APIs Xano

- [x] 1.1 Adicionar `prazo_entrega` nullable à tabela `fornecedor` e validar todos os XanoScript alterados.
- [ ] 1.2 Criar consulta de fornecedores protegida para gestor e verificar respostas 401 sem sessão e 403 para colaborador.
- [ ] 1.3 Criar cadastro e edição com CNPJ único, campos obrigatórios e prazo opcional; verificar CNPJ duplicado e preservação de prazo ausente.
- [ ] 1.4 Criar remoção protegida que exclui fornecedor sem produtos e recusa fornecedor vinculado; verificar que registros e vínculos permanecem intactos na recusa.

## 2. Integração Reflex

- [ ] 2.1 Criar lista e formulário de fornecedores para gestor e verificar cadastro, edição e remoção permitida após confirmação.
- [ ] 2.2 Substituir o campo textual de ID do fornecedor no formulário de produto por seleção do catálogo e verificar o ID enviado à API.
- [ ] 2.3 Exibir falha de carregamento do catálogo e impedir salvar produto sem fornecedor válido; verificar mensagens sem expor ações ao colaborador.

## 3. Verificação integrada

- [ ] 3.1 Validar no Xano que colaborador não acessa operações de fornecedores e que gestor conclui o fluxo CRUD permitido.
- [ ] 3.2 Validar no Reflex a seleção de fornecedor em produto, confirmação/cancelamento da remoção e bloqueio quando há produto vinculado.
- [ ] 3.3 Executar a suíte de testes, compilar o Reflex e validar a change OpenSpec antes de revisão.