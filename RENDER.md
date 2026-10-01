# Configuração no Render

## Build Command

```bash
pip install -r requirements.txt
```

## Start Command

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

## Environment Variables

Configure em **Environment**:

```text
DATABASE_URL=<URL do PostgreSQL do Render>
RESET_DATABASE=true
```

### Importante sobre RESET_DATABASE

Com `RESET_DATABASE=true`, o banco PostgreSQL será apagado e recriado sempre que o processo do backend iniciar. Isso normalmente ocorre após um deploy, mas também pode ocorrer após reinicializações/restarts do serviço.

Para desenvolvimento/testes, mantenha:

```text
RESET_DATABASE=true
```

Quando quiser preservar os dados:

```text
RESET_DATABASE=false
```

Não use `true` em um ambiente com dados que precisam ser mantidos.
