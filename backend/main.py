import os
from datetime import date

from fastapi import FastAPI

from backend.database import Base, engine, SessionLocal
from backend.models import Usuario
from backend.auth import gerar_hash
from backend.routes import usuarios
from backend.routes import moradores
from backend.routes import financeiro


RESET_DATABASE = os.getenv("RESET_DATABASE", "false").strip().lower() in {
    "1", "true", "yes", "sim"
}


# ATENÇÃO: quando habilitado, todos os dados do banco são apagados.
if RESET_DATABASE:
    print("RESET_DATABASE=true — apagando todas as tabelas...")
    Base.metadata.drop_all(bind=engine)
    print("Banco apagado com sucesso.")


Base.metadata.create_all(bind=engine)
print("Banco criado/atualizado com sucesso.")


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
