# Configuração Supabase - Let's Play

O projeto foi configurado com sucesso para utilizar o banco de dados Supabase.

## Alterações Realizadas:
1.  **Variáveis de Ambiente**: Criado arquivo `.env` com as credenciais fornecidas.
2.  **Configuração de Banco**: Atualizado `backend/database_config.py` para carregar o `.env` e utilizar SSL (obrigatório para Supabase).
3.  **Dependências**: Instaladas `pg8000` e `python-dotenv`.
4.  **Esquema de Banco**:
    *   Executada a criação de todas as tabelas base (`usuarios`, `salas`, `apostas`, etc.).
    *   Executada a migração específica para o sistema de torneios.
    *   Inseridas configurações iniciais (senha admin padrão: `3579`).

## Credenciais Atuais:
*   **Host**: `aws-1-sa-east-1.pooler.supabase.com`
*   **Database**: `postgres`
*   **User**: `postgres.kubvbqvpuwecrlwwmrvc`

## Próximos Passos:
Para rodar o backend localmente com esta configuração:
1. Instale as dependências: `pip install pg8000 python-dotenv flask flask-cors flask-socketio`
2. Execute o servidor: `python backend/main.py`
