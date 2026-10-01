import os
from datetime import date

from fastapi import FastAPI

from backend.database import Base, engine, SessionLocal
# Importa os modelos antes de resetar/criar o schema, garantindo que todas
# as tabelas estejam registradas no metadata do SQLAlchemy.
from backend import models  # noqa: F401
from backend.models import Usuario
from backend.auth import gerar_hash
from backend.routes import usuarios
from backend.routes import moradores
from backend.routes import financeiro


RESET_DATABASE = os.getenv("RESET_DATABASE", "false").strip().lower() in {
    "1", "true", "yes", "sim"
}


if RESET_DATABASE:
    print("RESET_DATABASE=true -> apagando o banco de dados...")
    Base.metadata.drop_all(bind=engine)
    print("Banco de dados apagado.")


Base.metadata.create_all(bind=engine)
print("Estrutura do banco verificada/criada.")


app = FastAPI()

app.include_router(usuarios.router)
app.include_router(moradores.router)
app.include_router(financeiro.router)


def criar_admin():
    db = SessionLocal()

    try:
        admin = db.query(Usuario).filter(
            Usuario.cpf == "00000000000"
        ).first()

        if not admin:
            novo_admin = Usuario(
                nome="Administrador",
                cpf="00000000000",
                nascimento=date(1990, 1, 1),
                senha_hash=gerar_hash("admin123"),
                tipo="SINDICO"
            )

            db.add(novo_admin)
            db.commit()
            print("Usuário administrador criado.")
        else:
            print("Usuário administrador já existe.")

    finally:
        db.close()


criar_admin()
