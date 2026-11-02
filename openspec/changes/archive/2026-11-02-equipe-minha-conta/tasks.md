## 1. Banco e backend Xano

- [x] 1.1 Adicionar `funcionario.salario` de forma aditiva, preservando registros existentes, e validar o schema da tabela
- [x] 1.2 Corrigir ou criar o provisionamento transacional de funcionário e usuário para usar hash de senha, validar CPF/login únicos e nunca persistir senha em texto puro
- [x] 1.3 Criar endpoints protegidos para listar, cadastrar, editar e inativar funcionários, retornando salário somente ao gestor e nunca retornando hash
- [x] 1.4 Ajustar endpoints de Minha conta para permitir alteração de login e senha somente ao colaborador, exigindo senha atual e mantendo a sessão válida
- [x] 1.5 Validar no endpoint de criação de pedido que o funcionário da sessão está ativo, preservando consultas de pedidos históricos, e verificar os scripts Xano

## 2. Cliente HTTP e estado Reflex

- [x] 2.1 Adicionar modelos e métodos do `XanoClient` para funcionários, provisionamento, edição, inativação e validações de erro, verificando os payloads
- [x] 2.2 Adicionar ao estado Reflex os campos e eventos de equipe e ajustar o carregamento de sessão/minha conta por perfil, verificando 401, 403 e erros de regra
- [x] 2.3 Atualizar a navegação e os componentes Reflex para exibir equipe somente ao gestor e Minha conta somente ao colaborador, verificando o isolamento visual por perfil

## 3. Interface da equipe e credenciais

- [x] 3.1 Criar formulário de funcionário com dados pessoais, cargo, salário e credencial inicial, verificando mensagens de CPF/login duplicados
- [x] 3.2 Criar listagem, edição e inativação de funcionários com confirmação, verificando que salário e ações administrativas não aparecem ao colaborador
- [x] 3.3 Ajustar Minha conta para alteração de login e senha pelo colaborador, verificando senha atual incorreta, login ocupado e sessão preservada

## 4. Testes e verificação integrada

- [x] 4.1 Adicionar testes de contrato do `XanoClient` para equipe e Minha conta, incluindo respostas 401, 403 e conflitos de unicidade
- [x] 4.2 Adicionar testes dos cenários críticos de hash, provisionamento atômico, inativação e bloqueio de novo pedido por funcionário inativo
- [x] 4.3 Executar validação OpenSpec, testes Python, compilação Reflex e validação Xano, verificando o fluxo gestor cadastra funcionário -> colaborador acessa -> altera senha -> gestor inativa -> novo acesso/pedido é bloqueado