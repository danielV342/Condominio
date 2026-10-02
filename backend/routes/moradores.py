from fastapi import APIRouter, Depends
from backend.database import SessionLocal
from backend.deps import apenas_sindico
from backend.models import Usuario

router = APIRouter()


@router.get("/moradores")
def listar_moradores(usuario=Depends(apenas_sindico)):

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