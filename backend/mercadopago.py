"""Cliente mínimo da API do Mercado Pago para cobranças Pix.

Segredos ficam somente em variáveis de ambiente (nunca no app Android):
  MP_ACCESS_TOKEN    token de acesso (teste ou produção)
  MP_WEBHOOK_SECRET  chave secreta do webhook (painel do Mercado Pago)
"""
import hashlib
import hmac
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx

API_URL = "https://api.mercadopago.com"
FUSO_BR = timezone(timedelta(hours=-3))
TIMEOUT = 20.0


class MercadoPagoErro(Exception):
    def __init__(self, mensagem: str, status_code: int | None = None):
        super().__init__(mensagem)
        self.status_code = status_code


def _headers(extra: dict | None = None) -> dict:
    token = os.getenv("MP_ACCESS_TOKEN", "").strip()
    if not token:
        raise MercadoPagoErro("MP_ACCESS_TOKEN não configurado.")
    headers = {"Authorization": f"Bearer {token}"}
    headers.update(extra or {})
    return headers


def criar_pagamento_pix(
    *,
    valor: float,
    descricao: str,
    email: str,
    referencia: str,
    expira_em: datetime,
    notification_url: str,
) -> dict:
    """Cria um pagamento Pix e devolve o JSON do Mercado Pago."""
    corpo = {
        "transaction_amount": round(float(valor), 2),
        "description": descricao[:200],
        "payment_method_id": "pix",
        "payer": {"email": email},
        "external_reference": referencia,
        "notification_url": notification_url,
        "date_of_expiration": expira_em.astimezone(FUSO_BR).strftime(
            "%Y-%m-%dT%H:%M:%S.000-03:00"
        ),
    }
    try:
        resposta = httpx.post(
            f"{API_URL}/v1/payments",
            json=corpo,
            headers=_headers({"X-Idempotency-Key": str(uuid.uuid4())}),
            timeout=TIMEOUT,
        )
    except httpx.HTTPError as exc:
        raise MercadoPagoErro(f"Falha de rede com o Mercado Pago: {exc}") from exc

    if resposta.status_code not in (200, 201):
        raise MercadoPagoErro(
            f"Mercado Pago recusou a criação do Pix: {resposta.text[:300]}",
            resposta.status_code,
        )
    return resposta.json()


def consultar_pagamento(payment_id: str) -> dict:
    """Busca o pagamento direto na API (fonte da verdade para confirmar o Pix)."""
    try:
        resposta = httpx.get(
            f"{API_URL}/v1/payments/{payment_id}",
            headers=_headers(),
            timeout=TIMEOUT,
        )
    except httpx.HTTPError as exc:
        raise MercadoPagoErro(f"Falha de rede com o Mercado Pago: {exc}") from exc

    if resposta.status_code != 200:
        raise MercadoPagoErro(
            f"Consulta do pagamento falhou: {resposta.text[:300]}",
            resposta.status_code,
        )
    return resposta.json()


def assinatura_valida(
    secret: str,
    x_signature: str | None,
    x_request_id: str | None,
    data_id: str | None,
) -> bool:
    """Valida o header x-signature conforme a documentação do Mercado Pago."""
    if not x_signature:
        return False

    partes = {}
    for trecho in x_signature.split(","):
        chave, _, valor = trecho.strip().partition("=")
        partes[chave] = valor

    ts, v1 = partes.get("ts"), partes.get("v1")
    if not ts or not v1:
        return False

    manifesto = ""
    if data_id:
        manifesto += f"id:{data_id.lower()};"
    if x_request_id:
        manifesto += f"request-id:{x_request_id};"
    manifesto += f"ts:{ts};"

    esperado = hmac.new(
        secret.encode(), manifesto.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(esperado, v1)
