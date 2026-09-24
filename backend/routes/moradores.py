from fastapi import APIRouter
from backend.database import SessionLocal
from backend.models import Usuario

router = APIRouter()


@router.get("/moradores")
def listar_moradores():

    db = SessionLocal()

    try:

        moradores = db.query(Usuario).all()

        return [
            {
                "id": morador.id,
                "nome": morador.nome,
                "cpf": morador.cpf,
                "nascimento": morador.nascimento,
                "tipo": morador.tipo
            }
            for morador in moradores
        ]

    finally:

        db.close()