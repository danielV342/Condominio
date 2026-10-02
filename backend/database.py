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


def garantir_colunas_pix():
    """Adiciona as colunas do Pix em bancos já existentes.

    Base.metadata.create_all() só cria tabelas novas; ele não altera tabelas que
    já existem. Assim não é preciso usar RESET_DATABASE=true (que apaga tudo).
    """
    from sqlalchemy import inspect, text

    inspetor = inspect(engine)
    if "pagamentos" not in inspetor.get_table_names():
        return

    existentes = {c["name"] for c in inspetor.get_columns("pagamentos")}
    novas = {
        "mp_payment_id": "VARCHAR(40)",
        "pix_copia_e_cola": "TEXT",
        "pix_expira_em": "TIMESTAMP",
    }
    with engine.begin() as conexao:
        for nome, tipo in novas.items():
            if nome not in existentes:
                conexao.execute(text(f"ALTER TABLE pagamentos ADD COLUMN {nome} {tipo}"))
