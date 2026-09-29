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

@router.post("/financeiro")
def criar_cobranca(data: dict):

    db = SessionLocal()

    try:

        usuario = db.query(Usuario).filter(
            Usuario.cpf == data["cpf"]
        ).first()

        if not usuario:
            return {
                "status": "erro",
                "mensagem": "Morador não encontrado"
            }

        pagamento = Pagamento(
            usuario_id=usuario.id,
            descricao=data["descricao"],
            valor=data["valor"],
            vencimento=data["vencimento"],
            status="PENDENTE"
        )

        db.add(pagamento)
        db.commit()
        db.refresh(pagamento)

        return {
            "status": "ok",
            "mensagem": "Cobrança criada",
            "id": pagamento.id
        }

    finally:
        db.close()