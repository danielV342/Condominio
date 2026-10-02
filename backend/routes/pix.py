import logging
import os
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from backend import mercadopago as mp
from backend.database import SessionLocal
from backend.deps import usuario_logado
from backend.models import Pagamento, Usuario

router = APIRouter()
log = logging.getLogger("pix")

VALIDADE_PIX_MINUTOS = 30


def _url_webhook() -> str:
    base = os.getenv("PUBLIC_BASE_URL", "https://condominio-vw2i.onrender.com").rstrip("/")
    return f"{base}/webhooks/mercadopago"


def _agora_utc() -> datetime:
    # Guardamos datas em UTC "naive" (sem fuso) no banco.
    return datetime.now(UTC).replace(tzinfo=None)


def _resposta(pagamento: Pagamento) -> dict:
    return {
        "txid": pagamento.mp_payment_id,
        "copia_e_cola": pagamento.pix_copia_e_cola,
        "valor": float(pagamento.valor),
        "expira_em": pagamento.pix_expira_em.isoformat() + "Z"
        if pagamento.pix_expira_em
        else None,
    }


@router.post("/financeiro/cobrancas/{pagamento_id}/pix")
def gerar_pix(pagamento_id: int, usuario=Depends(usuario_logado)):
    db = SessionLocal()
    try:
        pagamento = db.query(Pagamento).filter(Pagamento.id == pagamento_id).first()
        dono = (
            db.query(Usuario).filter(Usuario.id == pagamento.usuario_id).first()
            if pagamento
            else None
        )

        # 404 (e não 403) para não revelar a existência de cobranças de outros moradores.
        if not pagamento or not dono or dono.cpf != usuario.get("sub"):
            raise HTTPException(status_code=404, detail="Cobrança não encontrada.")

        if str(pagamento.status).upper() == "PAGO":
            raise HTTPException(status_code=409, detail="Esta cobrança já foi paga.")

        # Reaproveita o Pix ainda válido (idempotente).
        if (
            pagamento.mp_payment_id
            and pagamento.pix_copia_e_cola
            and pagamento.pix_expira_em
            and pagamento.pix_expira_em > _agora_utc() + timedelta(minutes=1)
        ):
            return _resposta(pagamento)

        expira_em = _agora_utc() + timedelta(minutes=VALIDADE_PIX_MINUTOS)
        try:
            criado = mp.criar_pagamento_pix(
                valor=pagamento.valor,
                descricao=pagamento.descricao,
                # O cadastro não tem e-mail; o Mercado Pago exige um e-mail do pagador.
                email=f"morador{dono.id}@meucondominio.app",
                referencia=str(pagamento.id),
                expira_em=expira_em.replace(tzinfo=UTC),
                notification_url=_url_webhook(),
            )
            dados = criado["point_of_interaction"]["transaction_data"]
            pagamento.mp_payment_id = str(criado["id"])
            pagamento.pix_copia_e_cola = dados["qr_code"]
            pagamento.pix_expira_em = expira_em
        except (mp.MercadoPagoErro, KeyError, TypeError) as exc:
            log.error("Erro ao gerar Pix da cobrança %s: %s", pagamento_id, exc)
            raise HTTPException(
                status_code=502,
                detail="Não foi possível gerar o Pix agora. Tente novamente.",
            )

        db.commit()
        return _resposta(pagamento)
    finally:
        db.close()


def _processar_notificacao(data_id: str) -> dict:
    try:
        pagamento_mp = mp.consultar_pagamento(data_id)
    except mp.MercadoPagoErro as exc:
        if exc.status_code == 404:
            return {"status": "ignorado", "motivo": "pagamento não encontrado"}
        raise

    if pagamento_mp.get("status") != "approved":
        return {"status": "ignorado", "motivo": f"status {pagamento_mp.get('status')}"}

    if pagamento_mp.get("payment_method_id") != "pix":
        return {"status": "ignorado", "motivo": "não é Pix"}

    try:
        pagamento_id = int(pagamento_mp.get("external_reference"))
    except (TypeError, ValueError):
        return {"status": "ignorado", "motivo": "sem referência"}

    db = SessionLocal()
    try:
        pagamento = db.query(Pagamento).filter(Pagamento.id == pagamento_id).first()
        if not pagamento:
            return {"status": "ignorado", "motivo": "cobrança inexistente"}

        if str(pagamento.status).upper() == "PAGO":
            return {"status": "ok", "motivo": "já estava paga"}

        pago = float(pagamento_mp.get("transaction_amount") or 0)
        if abs(pago - float(pagamento.valor)) > 0.01:
            log.error(
                "Valor divergente na cobrança %s: pago %.2f, esperado %.2f",
                pagamento_id, pago, float(pagamento.valor),
            )
            return {"status": "ignorado", "motivo": "valor divergente"}

        pagamento.status = "PAGO"
        pagamento.data_pagamento = datetime.now(mp.FUSO_BR).date()
        db.commit()
        return {"status": "ok", "motivo": "baixa realizada"}
    finally:
        db.close()


@router.post("/webhooks/mercadopago")
async def webhook_mercadopago(request: Request):
    try:
        corpo = await request.json()
    except Exception:
        corpo = {}
    if not isinstance(corpo, dict):
        corpo = {}

    tipo = request.query_params.get("type") or corpo.get("type")
    data_id = request.query_params.get("data.id") or (corpo.get("data") or {}).get("id")

    segredo = os.getenv("MP_WEBHOOK_SECRET", "").strip()
    if segredo:
        valido = mp.assinatura_valida(
            segredo,
            request.headers.get("x-signature"),
            request.headers.get("x-request-id"),
            str(data_id) if data_id else None,
        )
        if not valido:
            raise HTTPException(status_code=401, detail="Assinatura inválida.")
    else:
        log.warning("MP_WEBHOOK_SECRET não configurado: assinatura não validada.")

    if tipo != "payment" or not data_id:
        return {"status": "ignorado"}

    try:
        # Sempre confirma o pagamento direto na API do Mercado Pago.
        return await run_in_threadpool(_processar_notificacao, str(data_id))
    except mp.MercadoPagoErro as exc:
        log.error("Erro ao processar webhook %s: %s", data_id, exc)
        # 5xx faz o Mercado Pago tentar de novo mais tarde.
        raise HTTPException(status_code=500, detail="Erro ao processar notificação.")
