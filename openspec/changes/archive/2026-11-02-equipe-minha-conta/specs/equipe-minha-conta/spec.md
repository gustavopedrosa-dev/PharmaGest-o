## Purpose

Esta capacidade permite ao gestor manter a equipe e seus acessos, enquanto oferece ao colaborador uma forma segura de atualizar as próprias credenciais sem expor senhas ou alterar permissões.

## ADDED Requirements

### Requirement: Gestor administra funcionários

O sistema SHALL permitir que um gestor autenticado consulte, cadastre, edite e inative funcionários, incluindo salário, sem permitir essas operações ao colaborador.

#### Scenario: Gestor cadastra funcionário

- **WHEN** um gestor envia dados válidos de um novo funcionário
- **THEN** o sistema cria o funcionário e sua conta de acesso ativa, vinculadas entre si

#### Scenario: Colaborador tenta administrar funcionário

- **WHEN** um colaborador tenta consultar dados restritos, cadastrar, editar ou inativar funcionário
- **THEN** a API rejeita a operação com erro de permissão e não altera dados

#### Scenario: Gestor edita funcionário

- **WHEN** um gestor envia alterações válidas para um funcionário existente
- **THEN** o sistema atualiza os dados sem alterar o identificador, o histórico de pedidos ou o perfil da conta

#### Scenario: Gestor inativa funcionário

- **WHEN** um gestor solicita a saída de um funcionário
- **THEN** o sistema mantém o funcionário e seu histórico, inativa sua conta e impede novos acessos e atendimentos

### Requirement: Acesso inicial é provisionado com segurança

O sistema SHALL criar a conta do funcionário em operação atômica, armazenar somente a senha protegida por hash e entregar a senha inicial ao gestor somente no momento autorizado de provisionamento, sem persistir a senha em texto puro na resposta ou no banco.

#### Scenario: Provisionamento bem-sucedido

- **WHEN** um gestor cadastra funcionário com login disponível e senha inicial válida
- **THEN** o sistema cria funcionário e usuário vinculados, armazena o hash da senha e retorna a credencial inicial somente na resposta segura da operação

#### Scenario: CPF ou login já utilizado

- **WHEN** o gestor tenta cadastrar funcionário com CPF ou login já existente
- **THEN** o sistema rejeita a operação e não cria funcionário nem usuário parcial

#### Scenario: Falha durante o provisionamento

- **WHEN** qualquer etapa da criação de funcionário ou usuário falha
- **THEN** o sistema desfaz as alterações parciais e não deixa uma conta sem funcionário ou funcionário sem conta

### Requirement: Usuário inativo não acessa nem atende novos pedidos

O sistema SHALL validar a situação ativa da conta em cada sessão protegida e SHALL impedir que funcionário ou usuário inativo seja associado a novos pedidos, preservando pedidos históricos.

#### Scenario: Usuário inativado tenta acessar

- **WHEN** uma conta inativada tenta fazer login ou usa um token existente em uma rota protegida
- **THEN** a API recusa o acesso e não executa a operação

#### Scenario: Funcionário inativo registra pedido

- **WHEN** uma tentativa de criação de pedido está associada a um funcionário inativo
- **THEN** a API rejeita a operação e não cria pedido nem item parcial

#### Scenario: Histórico de funcionário inativo

- **WHEN** o gestor consulta pedidos registrados por funcionário que foi inativado
- **THEN** os pedidos históricos continuam disponíveis com a identificação original do atendente

### Requirement: Colaborador altera próprias credenciais

O sistema SHALL permitir que um colaborador ativo altere o próprio login e senha, exigindo a senha atual para a troca de senha e preservando seu perfil e vínculo com o funcionário.

#### Scenario: Colaborador altera próprio login

- **WHEN** um colaborador salva um login disponível na área Minha conta
- **THEN** somente o login da própria conta é atualizado e a sessão continua associada ao mesmo funcionário e perfil

#### Scenario: Colaborador troca própria senha

- **WHEN** um colaborador informa a senha atual correta e uma nova senha válida
- **THEN** somente a senha da própria conta é atualizada com hash e a sessão atual continua ativa

#### Scenario: Senha atual incorreta

- **WHEN** um colaborador informa uma senha atual incorreta
- **THEN** a API recusa a alteração, mantém a senha existente e não encerra a sessão válida

#### Scenario: Login escolhido já está em uso

- **WHEN** um colaborador tenta salvar um login utilizado por outra conta
- **THEN** a API recusa a alteração e mantém o login anterior

#### Scenario: Gestor acessa Minha conta

- **WHEN** um gestor tenta acessar ou chamar diretamente as operações de Minha conta destinadas ao colaborador
- **THEN** a interface não oferece essa área e a API rejeita a operação com erro de permissão

