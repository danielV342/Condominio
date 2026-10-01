# Deploy no Render

## Build Command

```bash
pip install -r requirements.txt
```

## Start Command

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

## Variáveis de ambiente

Configure no Render:

```text
DATABASE_URL=<URL do PostgreSQL do Render>
RESET_DATABASE=true
```

### RESET_DATABASE

- `true`: apaga todas as tabelas na inicialização, recria o banco e recria o administrador padrão.
- `false`: preserva os dados existentes e apenas cria tabelas que ainda não existirem.

**Atenção:** `RESET_DATABASE=true` é destrutivo. Use somente enquanto estiver iniciando/testando o sistema.

## Administrador padrão após um reset

```text
CPF: 00000000000
Senha: admin123
Tipo: SINDICO
```

Depois que o banco estiver pronto para uso, altere no Render:

```text
RESET_DATABASE=false
```
