## Context

Consulte `proposal.md` e `specs/identidade-autorizacao/spec.md` para motivação e comportamento esperado.

Auditoria realizada em 2026-10-11 no workspace Xano `Gustavo's Workspace` (ID 167469), branch `v1`. O CLI baixou 36 documentos sem incluir registros nem variáveis de ambiente; a comparação SHA-256 dos arquivos `.xs` locais e remotos não encontrou diferenças. Em 2026-10-12, o usuário confirmou que nenhuma tabela contém registros e que a identidade Quick Start `user` não é usada nem será utilizada.

No schema atual, `usuario` ainda tem `auth = false`, `senha_hash` como texto anulável, perfis diferentes dos dois papéis do produto e `ativo` anulável. Os índices únicos de `login` e `id_funcionario` já representam unicidade de login e vínculo 1:1; o índice único de `senha_hash` não é necessário. A tabela autenticável `user` e os endpoints, addon e funções associados são do Quick Start. `event_log` também é usado somente pelo fluxo Quick Start nos arquivos versionados. O DBML adicionado em `docs/banco-de-dados.dbml` documenta o modelo-alvo.

O Reflex ainda é o scaffold inicial; não existe cliente Xano no código. `rxconfig.py` registra os plugins Reflex e `requirements.txt` já inclui HTTPX. O `.gitignore` atual não exclui `.env`. O workspace Xano reporta `allow_push: false`, e o usuário informou que branches Xano exigem um plano pago. Como o workspace foi criado exclusivamente para este sistema, este design usa `v1` como ambiente de desenvolvimento desta Change, com aplicação manual pela interface Xano; ele não deve ser tratado como produção.

## Goals / Non-Goals

**Goals:**
- Usar `usuario` como única identidade de autenticação, vinculada 1:1 a `funcionario`.
- Aplicar autenticação, autorização por papel, sessão e alteração das credenciais próprias no backend e no Reflex.
- Permitir bootstrap manual e seguro do primeiro gestor, sem credenciais versionadas ou endpoint público permanente.
- Remover os artefatos Quick Start que dependem da identidade antiga, evitando referências quebradas à tabela removida.
- Manter configuração e token fora do navegador e tornar o contrato HTTP verificável.

**Non-Goals:**
- Implementar cadastro/gestão da equipe ou provisionamento de colaboradores pela tela Equipe.
- Implementar recuperação de senha por e-mail, refresh token, autorização de outras áreas de negócio ou credenciais administrativas no Reflex.
- Alterar os campos de domínio destinados a produtos, estoque, clientes, fornecedores, vendas ou receitas.

## Decisions

1. **`usuario` será a tabela autenticável.** Ativar `auth` nela, trocar `senha_hash` para o tipo `password` obrigatório, restringir `perfil_acesso` a um enum obrigatório com `gestor` e `colaborador`, e tornar `ativo` não anulável com padrão `true`. Manter os índices únicos de login e funcionário; remover o índice único de senha. O DBML e o XanoScript confirmam a relação 1:1 e que `password` é o tipo de credencial com hash. Alternativa rejeitada: mapear `user` para `usuario`, pois manteria duas identidades e regras de sincronização.

2. **Bootstrap manual como padrão.** Criar função executável no editor Xano, sem endpoint público. Recebe nome, CPF, login e senha durante a execução; verifica a existência de qualquer usuário `gestor`, inclusive inativo; cria funcionário com cargo `Gestor` e usuário ativo. A senha não pode constar no código, logs, retorno ou repositório. Se execução direta de função não for viável no plano, usar somente como alternativa um endpoint temporário protegido por segredo de ambiente, sem segredo no Reflex/Git, e removê-lo imediatamente após uso. Alternativa rejeitada: signup público.

3. **Autorização consulta o estado atual do banco.** Funções de autorização usam a identidade autenticada, buscam `perfil_acesso` e `ativo` em cada chamada e falham fechadas se a conta não existir, estiver inativa ou tiver perfil inválido. Token ausente, inválido, expirado ou associado a conta inativa significa sessão não autenticada e retorna HTTP 401; HTTP 403 fica reservado a usuário autenticado sem permissão para a operação. O frontend filtra navegação e protege experiência; não concede acesso. No futuro, cadastro de funcionário deve atribuir `colaborador` no backend, sem aceitar perfil do cliente.

4. **Token de oito horas sem refresh.** Xano emite token vinculado a `usuario`; endpoints de login/sessão fornecem somente dados não sensíveis do funcionário e perfil. O Reflex mantém `_token` somente em estado server-side e envia `Authorization: Bearer` pelo servidor. Logout limpa o estado local; não promete revogação de um token já emitido, que expira em até oito horas. Alternativa de refresh token fica fora do escopo inicial.

5. **Um único adaptador HTTP no Reflex.** Centralizar URL base, token e interpretação de respostas em `api/xano.py`. Ler `XANO_BASE_URL` do ambiente; versionar `.env.example` sem valores e adicionar `.env` ao `.gitignore`. O frontend aplica o mapeamento definido na spec: 401 encerra sessão, 403 preserva sessão, 4xx de regra apresenta mensagem do backend, 5xx/timeout preservam sessão e mostram indisponibilidade. Não incluir chave administrativa no cliente.

6. **Retirar o Quick Start como conjunto coerente.** Remover signup/login/me/reset, envio de boas-vindas, APIs de logs, addon e funções que consultam `user`; remover também `user` e `event_log`, que no export são estruturas exclusivas do Quick Start sem registros, conforme confirmação do usuário. Não substituir logs genéricos por auditoria nova nesta Change. Alternativa de apenas desativar o login legado rejeitada, pois deixaria APIs e referências sem uso e uma segunda identidade no workspace.

7. **Minha conta é simétrica para os dois perfis.** Ambos podem alterar somente o próprio login e senha. A troca de senha exige a senha atual correta; após a alteração, a sessão que realizou a operação permanece ativa. A API deriva o usuário do token; não aceita `id_usuario`, perfil ou associação a funcionário enviados pelo Reflex. Nenhum dos campos de perfil ou vínculo pode ser alterado nesta tela.

## Risks / Trade-offs

- [O tipo `password` pode ter diferenças de escrita/verificação em relação ao campo textual atual] → Não há dados para migrar; validar o schema durante a tarefa 2.1 e, após implementar o login na 2.3, verificar criação/comparação do hash com credenciais de teste na tarefa 4.1, antes de remover o Quick Start ou cadastrar credenciais reais.
- [Remover `user` pode afetar consumidor externo não conhecido] → O usuário confirmou que a tabela e Quick Start não são usados; antes de remover endpoints, verificar referências/dependências publicadas fora do repositório. Se houver consumidor, interromper a remoção e revisar o escopo.
- [Logout não revoga token roubado] → Usar HTTPS, não expor token ao browser e limitar a validade a oito horas; revogação/refresh ficam fora do escopo.
- [Perfil consultado a cada chamada acrescenta leitura ao banco] → Priorizar segurança e revogação imediata; medir somente se o volume futuro justificar otimização sem cache de autorização obsoleto.
- [Não há branch Xano isolado e o CLI não pode enviar alterações com `allow_push: false`] → Aplicar manualmente pela interface no workspace dedicado, somente após export de segurança; executar uma etapa por vez, testar antes de remover componentes antigos e manter export posterior para comparação. Não expor `v1` a usuários finais; preparar ambiente de produção separado antes do lançamento.
- [`.env` ainda não é ignorado pelo Git] → Incluir regra no `.gitignore` e revisar `git status` para garantir que nenhum segredo real seja staged.

## Migration Plan

1. Confirmar que `v1` está dedicado ao projeto e não está servindo usuários finais; baixar um export de segurança do workspace sem registros nem variáveis de ambiente e verificar que ele corresponde ao estado versionado.
2. Aplicar manualmente pela interface Xano uma etapa por vez em `v1`, começando pela autenticação de `usuario`; registrar cada alteração e validar o schema antes de seguir.
3. Implementar APIs de identidade e autorização e testá-las com contas de teste no próprio workspace; validar criação/comparação do hash junto com login válido/inválido e emissão/validação de token. Não cadastrar ainda credenciais reais de usuários finais.
4. Integrar o Reflex e executar os testes de contrato HTTP e os fluxos dos dois perfis. Manter os artefatos Quick Start existentes até os testes HTTP da tarefa 4.1 e o fluxo do Reflex passarem.
5. Remover `user`, `event_log` e os componentes Quick Start numa etapa controlada, depois dos testes acima; verificar que não restam referências no workspace.
6. Baixar um novo export sem registros nem variáveis de ambiente, comparar com o anterior e com `xano/`, revisar e atualizar os arquivos versionados. Em falha, interromper as alterações e restaurar manualmente os documentos do export de segurança pela interface Xano.
7. Antes de disponibilizar o sistema a usuários finais, preparar um ambiente de produção separado; só então executar o bootstrap com a credencial inicial real e validar o primeiro login.

