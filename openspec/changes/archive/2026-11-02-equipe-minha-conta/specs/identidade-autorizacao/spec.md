## MODIFIED Requirements

### Requirement: Gestor e colaborador gerenciam somente as próprias credenciais

O sistema SHALL permitir que somente um colaborador ativo altere o próprio login e senha, exigir a senha atual para a troca de senha, manter a sessão atual ativa após a troca e preservar a associação com o funcionário e o perfil. O sistema SHALL recusar logins que já estejam em uso e SHALL rejeitar gestores nessa capacidade.

#### Scenario: Gestor altera o próprio login

- **WHEN** um gestor tenta salvar um novo login na área Minha conta
- **THEN** a interface não oferece essa operação e a API responde erro de permissão sem alterar a conta

#### Scenario: Gestor troca a própria senha

- **WHEN** um gestor tenta trocar a senha na área Minha conta
- **THEN** a interface não oferece essa operação e a API responde erro de permissão sem alterar a conta

#### Scenario: Gestor não altera credenciais pela área Minha conta

- **WHEN** um gestor tenta acessar a área Minha conta ou chamar diretamente suas operações
- **THEN** o Reflex não oferece a área e a API responde erro de permissão sem alterar a conta

#### Scenario: Colaborador altera o próprio login

- **WHEN** um colaborador ativo salva um login disponível na área Minha conta
- **THEN** somente o login da sua própria conta é atualizado e o perfil permanece `colaborador`

#### Scenario: Colaborador troca a própria senha

- **WHEN** um colaborador ativo informa a senha atual correta e uma nova senha válida
- **THEN** somente a senha da sua própria conta é atualizada com hash, o perfil permanece `colaborador` e a sessão continua ativa

#### Scenario: Senha atual incorreta

- **WHEN** um colaborador informa uma senha atual incorreta ao tentar alterá-la
- **THEN** a API recusa a alteração, mantém a senha existente e a sessão atual

#### Scenario: Login escolhido já está em uso

- **WHEN** um colaborador tenta salvar um login utilizado por outra conta
- **THEN** a API recusa a alteração e o Reflex apresenta a mensagem de validação