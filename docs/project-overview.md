# Project Overview — FarmaGestão

## 1. Visão geral

O FarmaGestão é um sistema web de gestão para farmácias, desenvolvido como trabalho em grupo da disciplina de banco de dados (Sistemas de Informação, Impacta). O sistema centraliza o registro de vendas, o controle de estoque e o cadastro de produtos, clientes, fornecedores e funcionários.

O foco é a operação interna da farmácia: quem usa o sistema são o gestor e os colaboradores. O cliente final é apenas um cadastro mantido pela farmácia e não acessa o sistema.

O banco de dados foi modelado por jornadas (17 tabelas) e já está implementado no Xano. O frontend está sendo construído em Reflex (Python). Existe um protótipo HTML que serve de referência visual e funcional para as telas e para as permissões de cada perfil.

## 2. Problema

Farmácias que controlam vendas e estoque de forma manual ou dispersa (cadernos, planilhas, sistemas separados) têm pouca visibilidade do que vendem e do que precisa ser reposto. Isso leva a ruptura de estoque, dificuldade de acompanhar as vendas por produto e por canal e risco no controle de medicamentos controlados, que exigem receita. Além disso, sem perfis de acesso, qualquer pessoa da equipe enxerga e altera informações sensíveis, como salários e cadastros de fornecedores.

O FarmaGestão resolve isso reunindo essas rotinas em um único sistema, com regras de negócio aplicadas automaticamente e acesso separado por perfil.

## 3. Objetivos

O objetivo geral é oferecer ao gestor da farmácia controle e visibilidade sobre vendas, estoque e equipe, e dar aos colaboradores uma ferramenta simples para o atendimento diário.

Como objetivos específicos, o sistema deve:

- registrar vendas presenciais e online, identificando canal e atendente;
- manter o estoque atualizado a cada venda, impedir vendas acima do estoque disponível e sinalizar produtos abaixo do mínimo;
- garantir que medicamentos controlados só sejam vendidos com cliente cadastrado e receita informada;
- separar o que cada perfil pode ver e fazer;
- servir como base real para a modelagem de banco de dados apresentada na disciplina.

## 4. Público-alvo / usuários

O sistema tem dois perfis com login e um cadastro sem acesso.

O **gestor** acompanha a farmácia pelo painel, consulta vendas, clientes e estoque, e administra produtos, funcionários e fornecedores. Ele não registra vendas nem altera cadastros de clientes.

Os **colaboradores** (funcionários de balcão) registram vendas, cadastram e atualizam clientes e consultam o estoque. Também podem alterar o próprio usuário e senha. Não têm acesso a produtos, fornecedores, equipe ou ao painel do gestor, e portanto não veem salários.

O **cliente** é um registro mantido pela farmácia (nome, CPF, contato, endereço) e vinculado às suas compras. Não possui login.

## 5. Escopo

**Dentro do escopo inicial:** login por perfil (gestor e colaborador); painel do gestor; cadastro e manutenção de produtos, clientes, funcionários e fornecedores; registro de vendas com canal presencial ou online e forma de pagamento (dinheiro, cartão ou Pix); baixa automática de estoque; bloqueio de venda sem estoque suficiente; alerta de estoque abaixo do mínimo; exigência de receita para controlados; relatório simples de quantidade vendida por medicamento.

**Fora do escopo inicial:** controle de lotes e validade; pedidos de compra aos fornecedores; histórico completo de movimentação de estoque; cadastro detalhado de receitas médicas.

## 6. Principais funcionalidades

O sistema permitirá que o gestor acompanhe vendas e itens vendidos do dia, produtos abaixo do estoque mínimo e quantidade de funcionários ativos, além de consultar as vendas e a quantidade vendida por medicamento. O gestor poderá cadastrar, editar e remover produtos (com categoria, preço, estoque, estoque mínimo e marcação de controlado), funcionários e fornecedores. Ao cadastrar um funcionário, o sistema gera usuário e senha de acesso.

Os colaboradores poderão registrar vendas escolhendo cliente, canal, forma de pagamento (dinheiro, cartão ou Pix) e um ou mais produtos, com cálculo automático do total e baixa do estoque. O sistema impedirá a venda de produto sem estoque ou em quantidade maior que a disponível. Poderão cadastrar, editar e inativar clientes, consultar o estoque e atualizar os próprios dados de acesso.

| Módulo | Gestor | Colaborador |
|---|---|---|
| Painel (visão geral) | Acessa | Não acessa |
| Vendas | Consulta | Registra e consulta |
| Estoque | Consulta | Consulta |
| Produtos | Cadastra, edita e remove | Não acessa |
| Clientes | Consulta | Cadastra, edita e inativa |
| Equipe | Cadastra, edita e remove | Não acessa |
| Fornecedores | Cadastra, edita e remove | Não acessa |
| Minha conta | Não possui | Altera usuário e senha |

## 7. Requisitos e restrições importantes

- Toda venda identifica o canal (presencial ou online) e o atendente que a registrou.
- Venda que contenha medicamento controlado exige cliente cadastrado (não vale "cliente balcão") e número da receita médica.
- Não é possível registrar venda de produto sem estoque nem com quantidade maior que o estoque disponível, em qualquer canal. O estoque diminui automaticamente a cada venda e nunca fica negativo. Produto abaixo do mínimo é sinalizado como "repor". O protótipo ainda não implementa esse bloqueio.
- Salários e dados da equipe são visíveis somente ao gestor.
- Clientes não são apagados, e sim inativados, mantendo o histórico de compras. Cliente inativo não pode ser usado em novas vendas. Remoções e inativações pedem confirmação do usuário.
- O cliente não acessa o sistema nesta fase.
- O protótipo usa dados fictícios e serve como referência, não como código final.
- O projeto tem prazo e escopo definidos pela disciplina, então a prioridade é cobrir bem o fluxo principal antes de qualquer expansão.

## 8. Arquitetura tecnológica

- **Backend e banco de dados:** Xano, com o banco já criado (17 tabelas: cliente, endereco, pedido, item_pedido, venda, pagamento, receita, item_receita, funcionario, usuario, categoria, produto, fornecedor, lote, pedido_compra, item_pedido_compra, movimentacao_estoque) e lógica em XanoScript.
- **Frontend:** Reflex (Python), consumindo a API do Xano.
- **Especificação:** OpenSpec, para especificar cada mudança antes de implementar.
- **Versionamento:** Git e GitHub, com o projeto na pasta `projetos/connectdrogs`.
- **Assistente de IA:** GitHub Copilot.

## 9. Princípios de desenvolvimento

- Especificar antes de codar: cada mudança segue o ciclo do OpenSpec (Explore, Propose, Review, Apply, Archive).
- Mudanças pequenas e incrementais, uma funcionalidade por vez.
- As regras de negócio (controlados, estoque, permissões) ficam no backend, e o frontend apenas as apresenta.
- Nomes de entidades e campos seguem o modelo de dados já definido, em português.
- O protótipo orienta o comportamento das telas, mas o modelo de dados do Xano prevalece para a estrutura.

## 10. Segurança e integridade

Os aspectos mais críticos do sistema são o controle de acesso, a integridade do estoque e a rastreabilidade dos medicamentos controlados.

As permissões por perfil devem ser aplicadas no backend (Xano), e não apenas escondidas na interface. Senhas devem ser armazenadas com hash. O protótipo mostra senhas em texto puro e pré-preenchidas na tela de login, o que vale somente como demonstração.

Dados pessoais (CPF, telefone, endereço) e salários exigem cuidado de acesso e devem ser expostos só a quem precisa. Venda com controlado deve manter o vínculo entre cliente, receita e atendente. Vendas registradas não são editadas nem removidas pelas telas, para preservar o histórico. A validação de estoque deve acontecer no backend, no momento de registrar a venda, para que vendas simultâneas não deixem o estoque negativo. Como clientes estão ligados a vendas, eles não são apagados, e sim inativados. A mesma abordagem deve ser avaliada para produtos, funcionários e fornecedores.

## 11. Estratégia de desenvolvimento

Depois da documentação base, o desenvolvimento é dividido em duas changes do OpenSpec, cada uma com seu próprio ciclo (Explore, Propose, Review, Apply, Archive).

1. Preparar a documentação base: este overview, `docs/domain-model.md`, `AGENTS.md` e `openspec/config.yaml`.
2. **Change de backend (Xano):** autenticação e perfis de acesso (gestor e colaborador) aplicados na API; endpoints de produtos, clientes, vendas, equipe e fornecedores, além dos dados do painel; regras de negócio, que são o bloqueio de venda sem estoque suficiente, a baixa automática de estoque, a exigência de cliente cadastrado e receita para controlados e a inativação de clientes (com um campo de status no cliente, se ainda não existir).
3. **Change de design (frontend em Reflex):** telas de login, painel do gestor, vendas, estoque, produtos, clientes, equipe, fornecedores e minha conta, seguindo o protótipo; exibição das mensagens das regras (estoque insuficiente, receita obrigatória) e de clientes inativos; integração com a API entregue pela change de backend. O design pode começar em paralelo com base no protótipo, mas só é concluído quando a API estiver disponível.
4. Versionar no GitHub a cada change concluída e arquivada.
5. Reavaliar o escopo ao final, considerando itens como lotes, pedidos de compra e histórico de movimentação de estoque.

## 12. Fonte de verdade e documentação

- `docs/project-overview.md` (este documento): visão geral e direção do projeto.
- `docs/domain-model.md`: entidades, relacionamentos e regras de negócio.
- `AGENTS.md` e `openspec/config.yaml`: instruções e contexto para o assistente de IA.
- `openspec/`: especificações e mudanças em andamento.
- Banco de dados no Xano: fonte de verdade da estrutura de dados.
- Protótipo HTML: referência visual e de permissões, sem valor de especificação final.

Em caso de divergência, o modelo de domínio e as especificações prevalecem sobre o overview nos detalhes, e o overview prevalece sobre o protótipo.