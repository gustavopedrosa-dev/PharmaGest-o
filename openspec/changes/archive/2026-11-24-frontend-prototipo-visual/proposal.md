## Why

O frontend funcional já cobre os principais fluxos, mas sua apresentação ainda não corresponde ao protótipo visual aprovado. A reformulação é necessária agora para entregar uma experiência coerente, responsiva e compreensível para gestor e colaborador sem alterar as regras de negócio nem a segurança aplicada no backend.

## What Changes

- Reestruturar o layout compartilhado do Reflex com a identidade visual verde, fundos, cartões, tipografia, espaçamento e navegação definidos no protótipo.
- Reformular a tela de login com seleção visual de perfil, formulário em painel destacado e mensagens de erro claras, sem expor credenciais.
- Reformular o painel do gestor com cards de indicadores, alertas de estoque, ranking de produtos e histórico de vendas.
- Padronizar tabelas, abas, formulários, modais de confirmação, badges e estados vazios nas telas de produtos, estoque, clientes, equipe, fornecedores e vendas.
- Adaptar a navegação e os controles exibidos aos perfis de gestor e colaborador, preservando as proteções existentes.
- Garantir comportamento responsivo para telas menores, mantendo ações e informações essenciais acessíveis.
- Não alterar APIs Xano, regras de autorização, modelo de dados ou regras de estoque e vendas.

## Capabilities

### New Capabilities
- `frontend-experiencia-visual`: Define a apresentação visual, responsividade e consistência de interação do frontend conforme o protótipo.

### Modified Capabilities
- Nenhuma. As regras funcionais existentes permanecem inalteradas; a mudança trata da apresentação e da experiência visual.

## Impact

- Afeta principalmente `connectdrogs/connectdrogs.py` e a configuração/estilos do Reflex.
- Pode adicionar componentes auxiliares de apresentação e tokens de estilo, sem introduzir outro framework ou alterar o backend.
- Os testes de contrato Xano e os fluxos de autenticação, autorização, vendas e estoque devem continuar passando.
- A validação visual deverá cobrir login, painel do gestor e telas de operação dos dois perfis em viewport desktop e estreito.
