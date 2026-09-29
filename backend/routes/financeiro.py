from fastapi import APIRouter
from backend.database import SessionLocal
from backend.models import Pagamento, Usuario
from backend.schemas import PagamentoCreate
from backend.models import CobrancaRecorrente
from backend.schemas import CobrancaRecorrenteCreate

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
def criar_cobranca(data: PagamentoCreate):

    db = SessionLocal()

    try:

        usuario = db.query(Usuario).filter(
            Usuario.cpf == data.cpf
        ).first()

        if not usuario:
            return {
                "status": "erro",
                "mensagem": "Morador não encontrado"
            }

        pagamento = Pagamento(
            usuario_id=usuario.id,
            descricao=data.descricao,
            valor=data.valor,
            vencimento=data.vencimento,
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

@router.post("/financeiro/recorrente")
def criar_cobranca_recorrente(
    dados: CobrancaRecorrenteCreate
):

    db = SessionLocal()

    try:

        cobranca = CobrancaRecorrente(
            descricao=dados.descricao,
            valor=dados.valor,
            dia_vencimento=dados.dia_vencimento,
            ativo=True
        )

        db.add(cobranca)
        db.commit()
        db.refresh(cobranca)

        return {
            "status": "ok",
            "mensagem": "Cobrança recorrente criada",
            "id": cobranca.id
        }

    finally:

        db.close()

from datetime import date
from calendar import monthrange

def gerar_cobrancas_mensais():

    db = SessionLocal()

    try:

        recorrentes = db.query(CobrancaRecorrente).filter(
            CobrancaRecorrente.ativo == True
        ).all()

        hoje = date.today()

        moradores = db.query(Usuario).filter(
            Usuario.tipo == "MORADOR"
        ).all()

        for cobranca in recorrentes:

            dia = min(
                cobranca.dia_vencimento,
                monthrange(hoje.year, hoje.month)[1]
            )

            vencimento = date(
                hoje.year,
                hoje.month,
                dia
            )

            for morador in moradores:

                existe = db.query(Pagamento).filter(
                    Pagamento.usuario_id == morador.id,
                    Pagamento.vencimento == vencimento,
                    Pagamento.descricao == cobranca.descricao
                ).first()

                if not existe:

                    pagamento = Pagamento(
                        usuario_id=morador.id,
                        descricao=cobranca.descricao,
                        valor=cobranca.valor,
                        vencimento=vencimento,
                        status="PENDENTE"
                    )

                    db.add(pagamento)

        db.commit()

    finally:
        db.close()