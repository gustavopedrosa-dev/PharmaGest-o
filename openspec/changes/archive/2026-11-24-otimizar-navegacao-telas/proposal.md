## Why

Ao trocar de tela, o Reflex consulta a sessão e depois carrega os dados da rota em chamadas sequenciais ao Xano. Cada chamada cria uma nova conexão HTTP, aumentando a espera e o consumo de requisições durante a navegação.

## What Changes

- Validar a sessão das telas que carregam dados pela própria chamada protegida da rota, eliminando a consulta separada de sessão quando isso preservar o contrato de autenticação e autorização do backend.
- Manter a consulta de sessão nas telas que dependem dela para apresentar os dados da identidade, sem deixar de tratar respostas 401 e 403 conforme o comportamento atual.
- Reutilizar conexões HTTP entre as chamadas de leitura feitas durante o carregamento de uma tela.
- Continuar atualizando os dados da tela a cada navegação; não introduzir cache de dados que possa exibir informações desatualizadas.
- Adicionar verificações para garantir a redução de chamadas redundantes e a preservação dos redirecionamentos e mensagens de autorização.

## Capabilities

### New Capabilities

### Modified Capabilities
- `identidade-autorizacao`: esclarecer como telas protegidas validam a sessão ao carregar dados, preservando a autorização no backend e o tratamento de erros.

## Impact

- Reflex: carregadores de telas em `connectdrogs/connectdrogs.py`.
- Cliente HTTP do Xano em `api/xano.py`.
- Testes de contrato e navegação em `tests/`.
- Xano: nenhuma alteração de endpoints, dados ou regras de negócio; antes de remover uma consulta de sessão separada, confirmar que os endpoints de dados envolvidos validam token e perfil como especificado.
