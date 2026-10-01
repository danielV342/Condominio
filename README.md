# Meu Condomínio — Backend

Backend FastAPI + SQLAlchemy + PostgreSQL do sistema Meu Condomínio.

## Deploy no Render

**Build Command**

```bash
pip install -r requirements.txt
```

**Start Command**

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

## Variáveis de ambiente

Configure no Render:

- `DATABASE_URL`: URL de conexão do PostgreSQL.
- `RESET_DATABASE`: define se o banco será apagado e recriado na inicialização.

### RESET_DATABASE=true

Use durante o desenvolvimento quando quiser começar o banco do zero a cada deploy/reinicialização. O backend executa `drop_all()` e depois `create_all()`, recriando as tabelas conforme os modelos atuais. Em seguida, o administrador padrão é criado novamente.

**ATENÇÃO: `RESET_DATABASE=true` apaga TODOS os dados existentes.** Não use essa opção em um ambiente que precise preservar dados.

### RESET_DATABASE=false

Mantém os dados existentes entre os deploys e apenas executa `create_all()` para criar tabelas que ainda não existam.

## Administrador inicial

Quando o banco é recriado, o backend cria automaticamente:

- CPF: `00000000000`
- Senha: `admin123`
- Tipo: `SINDICO`

Altere essas credenciais antes de utilizar o sistema em um ambiente real.
