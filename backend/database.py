import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não foi configurada.")


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def garantir_colunas():
    """Adiciona colunas novas em tabelas que já existem.

    Base.metadata.create_all() só cria tabelas novas; ele não altera tabelas que
    já existem. Assim não é preciso usar RESET_DATABASE=true (que apaga tudo).
    """
    from sqlalchemy import inspect, text

    novas_colunas = {
        "pagamentos": {
            "mp_payment_id": "VARCHAR(40)",
            "pix_copia_e_cola": "TEXT",
            "pix_expira_em": "TIMESTAMP",
        },
        "usuarios": {
            "email": "VARCHAR(150)",
            "telefone": "VARCHAR(30)",
            "unidade": "VARCHAR(30)",
        },
    }

    inspetor = inspect(engine)
    tabelas = set(inspetor.get_table_names())

    with engine.begin() as conexao:
        for tabela, colunas in novas_colunas.items():
            if tabela not in tabelas:
                continue
            existentes = {c["name"] for c in inspetor.get_columns(tabela)}
            for nome, tipo in colunas.items():
                if nome not in existentes:
                    conexao.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}"))
