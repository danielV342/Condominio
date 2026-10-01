from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.auth import validar_token
from backend.database import get_db
from backend.models import Pagamento, Usuario, CobrancaRecorrente
from backend.schemas import CobrancaRecorrenteCreate


router = APIRouter()


def proximo_vencimento(dia: int, hoje: date | None = None) -> date:
    """Calcula o próximo vencimento a partir de hoje."""
    hoje = hoje or date.today()

    if hoje.day <= dia:
        dia_real = min(dia, monthrange(hoje.year, hoje.month)[1])
        return date(hoje.year, hoje.month, dia_real)

    if hoje.month == 12:
        ano, mes = hoje.year + 1, 1
    else:
        ano, mes = hoje.year, hoje.month + 1

    dia_real = min(dia, monthrange(ano, mes)[1])
    return date(ano, mes, dia_real)


def exigir_sindico(payload: dict):
    tipo = str(payload.get("tipo", "")).upper()

    if tipo != "SINDICO":
        raise HTTPException(
            status_code=403,
            detail="Apenas síndicos podem gerenciar cobranças."
        )


@router.get("/financeiro/dashboard")
def dashboard_financeiro(db: Session = Depends(get_db)):

    hoje = date.today()
    pagamentos = db.query(Pagamento).all()

    pagas = 0
    atrasadas = 0
    pendentes = 0
    valor_arrecadado = Decimal("0")
    valor_em_aberto = Decimal("0")

    for pagamento in pagamentos:
        valor = Decimal(str(pagamento.valor or 0))

        if pagamento.status == "PAGO":
            pagas += 1
            valor_arrecadado += valor

        elif pagamento.vencimento < hoje:
            atrasadas += 1
            valor_em_aberto += valor

        else:
            pendentes += 1
            valor_em_aberto += valor

    cobranca_ativa = (
        db.query(CobrancaRecorrente)
        .filter(CobrancaRecorrente.ativo.is_(True))
        .first()
    )

    cobranca_ativa_data = None

    if cobranca_ativa:
        cobranca_ativa_data = {
            "id": cobranca_ativa.id,
            "descricao": cobranca_ativa.descricao,
            "valor": float(cobranca_ativa.valor),
            "dia_vencimento": cobranca_ativa.dia_vencimento,
            "ativo": cobranca_ativa.ativo
        }

    return {
        "pagas": pagas,
        "atrasadas": atrasadas,
        "pendentes": pendentes,
        "valor_arrecadado": float(valor_arrecadado),
        "valor_em_aberto": float(valor_em_aberto),
        "cobranca_ativa": cobranca_ativa_data
    }


@router.post("/financeiro/recorrente")
def criar_cobranca_recorrente(
    dados: CobrancaRecorrenteCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(validar_token)
):
    """
    Cria uma cobrança recorrente e gera a cobrança do próximo vencimento
    para todos os moradores ativos.
    """

    exigir_sindico(payload)

    descricao = dados.descricao.strip()

    if not descricao:
        raise HTTPException(
            status_code=400,
            detail="A descrição da cobrança é obrigatória."
        )

    if dados.valor <= 0:
        raise HTTPException(
            status_code=400,
            detail="O valor deve ser maior que zero."
        )

    if not 1 <= dados.dia_vencimento <= 31:
        raise HTTPException(
            status_code=400,
            detail="O dia de vencimento deve estar entre 1 e 31."
        )

    try:
        # Mantém somente uma cobrança recorrente ativa.
        db.query(CobrancaRecorrente).filter(
            CobrancaRecorrente.ativo.is_(True)
        ).update(
            {"ativo": False},
            synchronize_session=False
        )

        cobranca = CobrancaRecorrente(
            descricao=descricao,
            valor=dados.valor,
            dia_vencimento=dados.dia_vencimento,
            ativo=True
        )

        db.add(cobranca)
        db.flush()

        vencimento = proximo_vencimento(dados.dia_vencimento)

        moradores = (
            db.query(Usuario)
            .filter(
                Usuario.tipo == "MORADOR",
                Usuario.ativo.is_(True)
            )
            .all()
        )

        criados = 0

        for morador in moradores:
            # Evita duplicar a mesma cobrança para o mesmo morador
            # no mesmo vencimento.
            existe = (
                db.query(Pagamento)
                .filter(
                    Pagamento.usuario_id == morador.id,
                    Pagamento.descricao == descricao,
                    Pagamento.vencimento == vencimento
                )
                .first()
            )

            if existe:
                continue

            pagamento = Pagamento(
                usuario_id=morador.id,
                descricao=descricao,
                valor=dados.valor,
                vencimento=vencimento,
                status="PENDENTE"
            )

            db.add(pagamento)
            criados += 1

        db.commit()
        db.refresh(cobranca)

        return {
            "sucesso": True,
            "mensagem": "Cobrança recorrente criada com sucesso.",
            "cobranca": {
                "id": cobranca.id,
                "descricao": cobranca.descricao,
                "valor": float(cobranca.valor),
                "dia_vencimento": cobranca.dia_vencimento,
                "ativo": cobranca.ativo
            },
            "vencimento_gerado": vencimento.isoformat(),
            "moradores_cobrados": criados
        }

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar cobrança: {str(e)}"
        )


@router.get("/financeiro/recorrente")
def obter_cobranca_recorrente(
    db: Session = Depends(get_db),
    payload: dict = Depends(validar_token)
):
    exigir_sindico(payload)

    cobranca = (
        db.query(CobrancaRecorrente)
        .filter(CobrancaRecorrente.ativo.is_(True))
        .first()
    )

    if not cobranca:
        return {
            "ativa": False,
            "cobranca": None
        }

    return {
        "ativa": True,
        "cobranca": {
            "id": cobranca.id,
            "descricao": cobranca.descricao,
            "valor": float(cobranca.valor),
            "dia_vencimento": cobranca.dia_vencimento,
            "ativo": cobranca.ativo
        }
    }


@router.delete("/financeiro/recorrente/{cobranca_id}")
def desativar_cobranca_recorrente(
    cobranca_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(validar_token)
):
    exigir_sindico(payload)

    cobranca = db.query(CobrancaRecorrente).filter(
        CobrancaRecorrente.id == cobranca_id
    ).first()

    if not cobranca:
        raise HTTPException(
            status_code=404,
            detail="Cobrança recorrente não encontrada."
        )

    cobranca.ativo = False
    db.commit()

    return {
        "sucesso": True,
        "mensagem": "Cobrança recorrente desativada."
    }
