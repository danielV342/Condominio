# Meu Condomínio - Backend

Backend FastAPI + SQLAlchemy + PostgreSQL para o aplicativo Meu Condomínio.

## Desenvolvimento / primeiro deploy

Defina `DATABASE_URL` e, se quiser começar com o banco zerado, `RESET_DATABASE=true`.

Com `RESET_DATABASE=true`, a inicialização executa:

1. `drop_all()` para apagar o schema existente;
2. `create_all()` para recriar as tabelas atuais;
3. criação do administrador padrão.

## Deploy no Render

Consulte `RENDER.md` para os comandos e variáveis de ambiente.

## Endpoints financeiros principais

- `GET /financeiro/dashboard`
- `POST /financeiro/recorrente`
- `GET /financeiro/recorrente`
- `DELETE /financeiro/recorrente/{id}`
