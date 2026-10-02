import os
import threading
import time
from datetime import date

from fastapi import FastAPI

from backend.database import Base, engine, SessionLocal, garantir_colunas
# Importa os modelos antes de resetar/criar o schema, garantindo que todas
# as tabelas estejam registradas no metadata do SQLAlchemy.
from backend import models  # noqa: F401
from backend.models import Usuario
from backend.auth import gerar_hash
from backend.routes import usuarios
from backend.routes import moradores
from backend.routes import financeiro
from backend.routes import pix
from backend.routes import perfil
from backend.routes import avisos
from backend.routes import chamados
from backend.routes import condominio


RESET_DATABASE = os.getenv("RESET_DATABASE", "false").strip().lower() in {
    "1", "true", "yes", "sim"
}

# Só apaga o banco uma vez, mesmo que a preparação precise ser repetida.
_reset_pendente = RESET_DATABASE


def inicializar_banco():
    """Cria tabelas, adiciona colunas novas e garante o administrador."""
    global _reset_pendente

    if _reset_pendente:
        print("RESET_DATABASE=true -> apagando o banco de dados...", flush=True)
        Base.metadata.drop_all(bind=engine)
        _reset_pendente = False
        print("Banco de dados apagado.", flush=True)

    Base.metadata.create_all(bind=engine)
    garantir_colunas()
    criar_admin()
    print("Banco de dados pronto.", flush=True)


def _inicializar_com_tentativas():
    tentativa = 0
    while True:
        tentativa += 1
        try:
            inicializar_banco()
            return
        except Exception as exc:  # noqa: BLE001
            print(f"Banco ainda não está pronto (tentativa {tentativa}): {exc}", flush=True)
            time.sleep(min(5 * tentativa, 30))


app = FastAPI()


@app.get("/")
def raiz():
    """Rota simples para checar se o servidor está no ar."""
    return {"status": "ok"}

app.include_router(usuarios.router)
app.include_router(moradores.router)
app.include_router(financeiro.router)
app.include_router(pix.router)
app.include_router(perfil.router)
app.include_router(avisos.router)
app.include_router(chamados.router)
app.include_router(condominio.router)


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


# Tenta preparar o banco já na subida (rápido no caso normal). Se falhar, por exemplo
# porque a versão antiga do app ainda segura um bloqueio durante o deploy, o servidor
# abre a porta mesmo assim e continua tentando em segundo plano.
try:
    inicializar_banco()
except Exception as exc:  # noqa: BLE001
    print(f"Falha ao preparar o banco na subida: {exc}", flush=True)
    print("O servidor vai abrir a porta e tentar de novo em segundo plano.", flush=True)
    threading.Thread(target=_inicializar_com_tentativas, daemon=True).start()
