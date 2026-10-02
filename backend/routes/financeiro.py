from calendar import monthrange
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from backend.database import SessionLocal
from backend.models import Pagamento, Usuario, CobrancaRecorrente
from backend.schemas import CobrancaRecorrenteCreate
from backend.deps import apenas_sindico, usuario_logado

router = APIRouter()


def proximo_vencimento(dia: int, hoje: date | None = None) -> date:
    hoje = hoje or date.today()

    dia = min(dia, monthrange(hoje.year, hoje.month)[1])
    candidato = date(hoje.year, hoje.month, dia)

    if candidato >= hoje:
        return candidato

    if hoje.month == 12:
        ano, mes = hoje.year + 1, 1
    else:
        ano, mes = hoje.year, hoje.month + 1

    dia = min(dia, monthrange(ano, mes)[1])
    return date(ano, mes, dia)


@router.get("/financeiro/dashboard")
def dashboard_financeiro(usuario=Depends(apenas_sindico)):
    db = SessionLocal()

    try:
        hoje = date.today()
        pagamentos = db.query(Pagamento).all()

        pagas = 0
        atrasadas = 0
        pendentes = 0
        valor_arrecadado = 0.0
        valor_em_aberto = 0.0

        for pagamento in pagamentos:
            valor = float(pagamento.valor or 0)

            if str(pagamento.status).upper() == "PAGO":
                pagas += 1
                valor_arrecadado += valor
            elif pagamento.vencimento and pagamento.vencimento < hoje:
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
                "ativo": cobranca_ativa.ativo,
            }

        return {
            "pagas": pagas,
            "atrasadas": atrasadas,
            "pendentes": pendentes,
            "valor_arrecadado": round(valor_arrecadado, 2),
            "valor_em_aberto": round(valor_em_aberto, 2),
            "cobranca_ativa": cobranca_ativa_data,
        }
    finally:
        db.close()


@router.post("/financeiro/recorrente")
def criar_cobranca_recorrente(
    dados: CobrancaRecorrenteCreate,
    usuario=Depends(usuario_logado),
):
    if str(usuario.get("tipo", "")).upper() != "SINDICO":
        raise HTTPException(status_code=403, detail="Apenas o síndico pode criar cobranças.")

    descricao = dados.descricao.strip()
    if not descricao:
        raise HTTPException(status_code=400, detail="A descrição é obrigatória.")
    if dados.valor <= 0:
        raise HTTPException(status_code=400, detail="O valor deve ser maior que zero.")
    if not 1 <= dados.dia_vencimento <= 31:
        raise HTTPException(status_code=400, detail="O dia de vencimento deve estar entre 1 e 31.")

    db = SessionLocal()
    try:
        # Mantém apenas uma cobrança recorrente ativa.
        db.query(CobrancaRecorrente).filter(
            CobrancaRecorrente.ativo.is_(True)
        ).update({CobrancaRecorrente.ativo: False}, synchronize_session=False)

        cobranca = CobrancaRecorrente(
            descricao=descricao,
            valor=dados.valor,
            dia_vencimento=dados.dia_vencimento,
            ativo=True,
        )
        db.add(cobranca)
        db.flush()

        vencimento = proximo_vencimento(dados.dia_vencimento)

        moradores = db.query(Usuario).filter(Usuario.ativo.is_(True)).all()
        moradores = [
            morador for morador in moradores
            if str(morador.tipo).upper() == "MORADOR"
        ]

        print("TOTAL USUÁRIOS ATIVOS:", len(
            db.query(Usuario).filter(Usuario.ativo.is_(True)).all()
            ))

        print("MORADORES ENCONTRADOS:", len(moradores))

        for morador in moradores:
            print(
            "MORADOR:",
            morador.id,
            morador.nome,
            morador.cpf,
            morador.tipo,
            morador.ativo
        )

        criados = 0
        for morador in moradores:
            existe = db.query(Pagamento.id).filter(
                Pagamento.usuario_id == morador.id,
                Pagamento.vencimento == vencimento,
                Pagamento.descricao == descricao,
            ).first()

            if existe:
                continue

            db.add(Pagamento(
                usuario_id=morador.id,
                descricao=descricao,
                valor=dados.valor,
                vencimento=vencimento,
                status="PENDENTE",
                data_pagamento=None,
            ))
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
                "ativo": cobranca.ativo,
            },
            "vencimento_gerado": vencimento,
            "moradores_cobrados": criados,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar cobrança: {exc}")
    finally:
        db.close()


@router.get("/financeiro/recorrente")
def listar_cobranca_recorrente():
    db = SessionLocal()
    try:
        cobranca = (
            db.query(CobrancaRecorrente)
            .filter(CobrancaRecorrente.ativo.is_(True))
            .first()
        )
        if not cobranca:
            return {"cobranca": None}

        return {
            "cobranca": {
                "id": cobranca.id,
                "descricao": cobranca.descricao,
                "valor": float(cobranca.valor),
                "dia_vencimento": cobranca.dia_vencimento,
                "ativo": cobranca.ativo,
            }
        }
    finally:
        db.close()


@router.delete("/financeiro/recorrente/{cobranca_id}")
def desativar_cobranca_recorrente(
    cobranca_id: int,
    usuario=Depends(usuario_logado),
):
    if str(usuario.get("tipo", "")).upper() != "SINDICO":
        raise HTTPException(status_code=403, detail="Apenas o síndico pode desativar cobranças.")

    db = SessionLocal()
    try:
        cobranca = db.query(CobrancaRecorrente).filter(
            CobrancaRecorrente.id == cobranca_id
        ).first()

        if not cobranca:
            raise HTTPException(status_code=404, detail="Cobrança recorrente não encontrada.")

        cobranca.ativo = False
        db.commit()
        return {"sucesso": True, "mensagem": "Cobrança recorrente desativada."}
    finally:
        db.close()

@router.get("/financeiro/cobrancas/{cpf}")
def listar_cobrancas_por_cpf(cpf: str, usuario=Depends(usuario_logado)):
    db = SessionLocal()

    try:
        # Remove pontuação do CPF, caso venha como 123.456.789-00
        cpf_limpo = "".join(filter(str.isdigit, cpf))

        # Morador só vê as próprias cobranças; síndico vê as de qualquer morador.
        cpf_token = "".join(filter(str.isdigit, str(usuario.get("sub", ""))))
        eh_sindico = str(usuario.get("tipo", "")).upper() == "SINDICO"
        if not eh_sindico and cpf_token != cpf_limpo:
            raise HTTPException(
                status_code=403,
                detail="Você não pode ver as cobranças de outro morador."
            )

        usuario = db.query(Usuario).filter(
            Usuario.cpf == cpf_limpo
        ).first()

        if not usuario:
            raise HTTPException(
                status_code=404,
                detail="Usuário não encontrado."
            )

        pagamentos = db.query(Pagamento).filter(
            Pagamento.usuario_id == usuario.id
        ).order_by(
            Pagamento.vencimento.desc()
        ).all()

        cobrancas = []

        for pagamento in pagamentos:
            cobrancas.append({
                "id": pagamento.id,
                "descricao": pagamento.descricao,
                "valor": float(pagamento.valor or 0),
                "vencimento": pagamento.vencimento,
                "status": pagamento.status,
                "data_pagamento": pagamento.data_pagamento,
            })

        return {
            "usuario": {
                "id": usuario.id,
                "nome": usuario.nome,
                "cpf": usuario.cpf,
            },
            "cobrancas": cobrancas
        }

    finally:
        db.close()

@router.get("/financeiro/pagamentos/debug")
def debug_pagamentos(usuario=Depends(apenas_sindico)):
    db = SessionLocal()

    try:
        pagamentos = db.query(Pagamento).all()

        return [
            {
                "id": p.id,
                "usuario_id": p.usuario_id,
                "descricao": p.descricao,
                "valor": float(p.valor or 0),
                "vencimento": p.vencimento,
                "status": p.status,
            }
            for p in pagamentos
        ]

    finally:
        db.close()