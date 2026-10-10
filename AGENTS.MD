<!-- reflex managed begin (do not edit inside this block; add custom content outside the markers) -->
# Agents

This project uses the **Reflex agent skills** � up-to-date knowledge for building full-stack Python web apps with [Reflex](https://reflex.dev). Install them first, then use them as described below.

## Installing the Skills

Before working on this project, make sure the Reflex skills are available to you.

### Claude Code

If the skills are not already available, install them yourself by running these shell commands:

```bash
claude plugin marketplace add reflex-dev/agent-skills
claude plugin install reflex@reflex-agent-skills
```

Newly installed plugins load on the next session. After installing, tell the user to restart the session so the skills auto-load; until then, read the skill files directly from `~/.claude/plugins/` when you need them.

### Other agents (Cursor, OpenCode, Codex, Pi)

```
npx skills add reflex-dev/agent-skills
```

Or clone https://github.com/reflex-dev/agent-skills and copy the `skills/` folders into your agent's skill directory (see the repo README for paths).

### Verifying

Before writing or editing any Reflex code, confirm these three skills are available: `reflex-docs`, `setup-python-env`, and `reflex-process-management`. If they are not, STOP and run the install step above � do not proceed without them.

## Using the Skills

### Reflex documentation

For anything about Reflex APIs � components, state management, events, styling, database, routing, authentication � use the **reflex-docs** skill rather than relying on memory. It carries current, version-accurate docs.

### Initializing a new Reflex project

When starting a new Reflex project or setting up a development environment, you **must** follow the **setup-python-env** skill before doing anything else.

Do not skip any steps. Do not assume a virtual environment or Reflex is already available � always verify first by following the skill's instructions in order.

After the environment is ready and Reflex is installed, run:

```bash
reflex init
```

Then proceed with the user's request.

### Managing a Reflex process

When you need to compile, run, reload, or debug a Reflex application, follow the **reflex-process-management** skill for the correct sequence and error investigation steps.
<!-- reflex managed end -->

# AGENTS.md

Instruções para os agentes de IA que trabalham no FarmaGestão. O `docs/project-overview.md` explica o projeto. Este arquivo explica como o agente deve atuar dentro dele.

## Documentação

Antes de realizar alterações significativas, consultar os documentos de contexto do projeto:

- `docs/project-overview.md`: visão, escopo, perfis de acesso e regras principais.
- `docs/domain-model.md`: entidades, relacionamentos e regras estruturais.
- `docs/prototipo/farmagestao-prototipo.html`: referência visual das telas e das permissões de cada perfil.

Em caso de divergência, o `domain-model.md` e as especificações do OpenSpec prevalecem nos detalhes, o `project-overview.md` prevalece sobre o protótipo, e o banco no Xano é a fonte de verdade da estrutura de dados. O protótipo difere do escopo em alguns pontos: não bloqueia venda sem estoque, remove clientes e funcionários em vez de inativá-los, não tem forma de pagamento, trata a categoria como texto livre, guarda um endereço único por cliente, não identifica atendente nas vendas online e usa uma conta fixa para o gestor (no modelo, o gestor é um funcionário). Nesses pontos, seguir o overview e o domain-model.

Não duplicar a documentação neste arquivo nem nas especificações. Referenciar o documento de origem.

## Arquitetura

- Respeitar as tecnologias definidas no projeto: Xano (backend e banco de dados) e Reflex (frontend em Python).
- Não introduzir tecnologias alternativas sem justificativa.
- O estoque fica no próprio produto (quantidade em estoque e estoque mínimo) e é reduzido diretamente pela venda.
- Não usar as tabelas `lote`, `pedido_compra`, `item_pedido_compra` e `movimentacao_estoque`, que estão fora do escopo inicial.
- Seguir os nomes de entidades e campos do modelo de dados, em português.

## Código

- Reutilizar código existente quando apropriado e evitar duplicação.
- Não modificar funcionalidades não relacionadas à mudança atual sem justificativa.
- Manter mudanças pequenas e incrementais.
- Clientes e usuários de funcionários não são apagados, e sim inativados.

## Segurança

- Regras de autorização por perfil (gestor e colaborador) devem ser aplicadas no backend, e não apenas escondidas na interface.
- Regras de negócio, como bloqueio de venda sem estoque suficiente e exigência de receita para controlados, são validadas no backend. O frontend apenas apresenta o resultado.
- Senhas são armazenadas com hash. Nunca versionar credenciais reais.
- Salários e dados pessoais só são expostos a quem tem permissão.

## Desenvolvimento

- Mudanças devem utilizar OpenSpec: Explore, Propose, Review, Apply e Archive.
- As changes são verticais: cada uma entrega uma funcionalidade completa (Xano e Reflex) e pode ser testada isoladamente, sem quebrar o que já funciona.
- Ajustes de banco são aditivos e limitados ao que a change precisa: campos novos opcionais ou com valor padrão, sem apagar nem alterar o que outras changes usam.
- Trabalhar em um branch do Git por change e integrar somente depois da verificação.
- Implementar apenas o que está especificado na change em andamento.

## Testes

- Mudanças funcionais devem possuir estratégia de verificação, definida na especificação da change.
- Verificar ao menos os fluxos críticos: permissões por perfil, venda bloqueada sem estoque suficiente e venda de controlado sem receita.
