from fastapi import APIRouter
from datetime import date

from backend.database import SessionLocal
from backend.models import (
    Pagamento,
    Usuario,
    CobrancaRecorrente
)

router = APIRouter()


@router.get("/financeiro/dashboard")
def dashboard_financeiro():

    db = SessionLocal()

    try:

        hoje = date.today()

        # Todas as cobranças
        pagamentos = db.query(Pagamento).all()

        # Quantidade de cobranças pagas
        pagas = 0

        # Quantidade de cobranças atrasadas
        atrasadas = 0

        # Quantidade de cobranças pendentes
        pendentes = 0

        # Valores
        valor_arrecadado = 0
        valor_em_aberto = 0

        for pagamento in pagamentos:

            if pagamento.status == "PAGO":

                pagas += 1

                valor_arrecadado += pagamento.valor

            elif pagamento.vencimento < hoje:

                atrasadas += 1

                valor_em_aberto += pagamento.valor

            else:

                pendentes += 1

                valor_em_aberto += pagamento.valor

        # Cobrança recorrente ativa
        cobranca_ativa = db.query(
            CobrancaRecorrente
        ).filter(
            CobrancaRecorrente.ativo == True
        ).first()

        if cobranca_ativa:

            cobranca_ativa_data = {
                "id": cobranca_ativa.id,
                "descricao": cobranca_ativa.descricao,
                "valor": cobranca_ativa.valor,
                "dia_vencimento": cobranca_ativa.dia_vencimento,
                "ativo": cobranca_ativa.ativo
            }

        else:

            cobranca_ativa_data = None

        return {

            "pagas": pagas,

            "atrasadas": atrasadas,

            "pendentes": pendentes,

            "valor_arrecadado": valor_arrecadado,

            "valor_em_aberto": valor_em_aberto,

            "cobranca_ativa": cobranca_ativa_data
        }

    finally:

        db.close()