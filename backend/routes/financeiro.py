from fastapi import APIRouter
from backend.database import SessionLocal
from backend.models import Pagamento, Usuario

router = APIRouter()


@router.get("/financeiro/{cpf}")
def listar_pagamentos(cpf: str):

    db = SessionLocal()

    try:

        usuario = db.query(Usuario).filter(
            Usuario.cpf == cpf
        ).first()

        if not usuario:

            return {
                "status": "erro",
                "mensagem": "Usuário não encontrado"
            }

        pagamentos = db.query(Pagamento).filter(
            Pagamento.usuario_id == usuario.id
        ).all()

        return [
            {
                "id": pagamento.id,
                "descricao": pagamento.descricao,
                "valor": pagamento.valor,
                "vencimento": pagamento.vencimento,
                "status": pagamento.status,
                "data_pagamento": pagamento.data_pagamento
            }
            for pagamento in pagamentos
        ]

    finally:

        db.close()