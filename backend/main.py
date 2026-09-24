from fastapi import FastAPI

from backend.database import Base, engine, SessionLocal
from backend.models import Usuario
from backend.auth import gerar_hash
from backend.routes import usuarios
from backend.routes import moradores

from datetime import date



Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(usuarios.router)
app.include_router(moradores.router)

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