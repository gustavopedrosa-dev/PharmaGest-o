## Context

Consulte `proposal.md` para a motivação. A autenticação existente usa as tabelas `usuario` e `funcionario`, sessão server-side e a função de autorização por perfil. A spec principal de identidade já define login, hash, sessão e troca de credenciais, mas ainda descreve gestores usando a área Minha conta, em conflito com o overview do projeto. Esta change também precisa preservar pedidos históricos e impedir novos atendimentos por contas inativas.

## Goals / Non-Goals

**Goals:**

- Entregar administração de funcionários e provisionamento de contas em uma operação protegida.
- Garantir hash de senha e ausência de credenciais persistidas em texto puro.
- Manter consistentes as relações funcionário-usuário e funcionário-pedido.
- Permitir a troca segura de credenciais somente pelo colaborador.
- Expor salário apenas em consultas autorizadas do gestor.

**Non-Goals:**

- Recuperação de senha por e-mail ou fluxo de convite externo.
- Portal do funcionário ou do cliente.
- Folha de pagamento, permissões granulares além de gestor/colaborador ou auditoria completa.
- Exclusão física de funcionários, usuários ou pedidos.

## Decisions

1. **Criar funcionário e usuário em transação.**
   A criação será atômica para impedir registros órfãos. Uma alternativa de endpoints independentes foi descartada porque uma falha entre as chamadas poderia deixar funcionário sem acesso ou usuário sem funcionário.

2. **Usar as primitivas de segurança do Xano para hash e verificação.**
   A senha inicial e a nova senha serão transformadas em hash no backend, e a senha atual será verificada antes da troca. Não será aceito gravar diretamente o valor recebido em `senha_hash`.

3. **Gerar credencial inicial somente no provisionamento autorizado.**
   O gestor receberá a senha inicial uma única vez na resposta controlada da criação, enquanto consultas posteriores nunca retornarão senha nem hash. Persistir ou exibir novamente a senha foi descartado por risco de exposição.

4. **Restringir Minha conta ao colaborador no backend e no Reflex.**
   O menu será condicionado ao perfil, mas os endpoints também exigirão `colaborador`. Ocultar a opção sem proteção na API não é suficiente.

5. **Inativar o usuário para desligamento.**
   A saída do funcionário altera a situação da conta e preserva as referências dos pedidos. Exclusão física foi descartada por quebrar a rastreabilidade do atendente.

6. **Adicionar salário de forma aditiva.**
   O campo `funcionario.salario` será opcional ou terá valor padrão compatível com dados existentes, e os endpoints de colaborador não o retornarão. O frontend não será considerado mecanismo de segurança.

7. **Validar atendente ativo na criação de pedido.**
   A API usará a sessão atual e a situação do usuário/funcionário antes de criar pedido. Consultas históricas continuarão incluindo funcionários inativos.

## Risks / Trade-offs

- **[Risco]** Uma senha inicial retornada ao gestor pode ser compartilhada. **Mitigação:** retornar somente na criação, exigir troca posterior em evolução futura e nunca persistir texto puro.
- **[Risco]** Dados atuais podem não possuir salário. **Mitigação:** migração aditiva com campo opcional ou padrão nulo e normalização nos payloads.
- **[Risco]** Alterar a regra de Minha conta pode divergir da interface atual. **Mitigação:** atualizar simultaneamente navegação, rota, API e testes por perfil.
- **[Trade-off]** Sem recuperação de senha, perda da senha inicial exige intervenção autorizada do gestor ou do ambiente Xano. **Mitigação:** manter o escopo explícito e não criar recuperação insegura nesta change.

## Migration Plan

1. Adicionar salário de forma aditiva e publicar endpoints de equipe protegidos.
2. Publicar a criação transacional de funcionário e usuário, com hash e validações de unicidade.
3. Atualizar a validação de pedidos e as rotas de Minha conta.
4. Publicar a tela Reflex e executar testes por perfil, hash, inativação e histórico.
5. Em caso de rollback, remover a exposição das novas telas/endpoints sem apagar funcionários, usuários ou pedidos; o campo de salário pode permanecer sem afetar versões anteriores.