import hashlib
import hmac
import os
from datetime import date, datetime, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_pix.db")
os.environ.setdefault("RESET_DATABASE", "true")

import pytest
from fastapi.testclient import TestClient

from backend import mercadopago as mp
from backend.auth import criar_token, gerar_hash
from backend.database import SessionLocal
from backend.main import app
from backend.models import Pagamento, Usuario

client = TestClient(app)


def _usuario(cpf, tipo="MORADOR"):
    db = SessionLocal()
    u = Usuario(nome=f"U{cpf}", cpf=cpf, nascimento=date(2000, 1, 1),
                senha_hash=gerar_hash("x"), tipo=tipo)
    db.add(u)
    db.commit()
    uid = u.id
    db.close()
    return uid


def _pagamento(uid, valor=350.0, status="PENDENTE"):
    db = SessionLocal()
    p = Pagamento(usuario_id=uid, descricao="Condomínio", valor=valor,
                  vencimento=date(2026, 10, 10), status=status)
    db.add(p)
    db.commit()
    pid = p.id
    db.close()
    return pid


def _auth(cpf, tipo="MORADOR"):
    return {"Authorization": f"Bearer {criar_token({'sub': cpf, 'tipo': tipo})}"}


@pytest.fixture
def mp_falso(monkeypatch):
    chamadas = {"criar": 0}

    def criar(**kw):
        chamadas["criar"] += 1
        assert kw["valor"] == 350.0  # valor vem do banco
        return {"id": 9000 + chamadas["criar"],
                "point_of_interaction": {"transaction_data": {"qr_code": "000201PIXFAKE6304ABCD"}}}

    monkeypatch.setattr(mp, "criar_pagamento_pix", criar)
    monkeypatch.delenv("MP_WEBHOOK_SECRET", raising=False)
    return chamadas


def test_gera_pix_e_reaproveita(mp_falso):
    uid = _usuario("10000000001")
    pid = _pagamento(uid)
    h = _auth("10000000001")

    r1 = client.post(f"/financeiro/cobrancas/{pid}/pix", headers=h)
    assert r1.status_code == 200
    assert r1.json()["copia_e_cola"] == "000201PIXFAKE6304ABCD"
    assert r1.json()["valor"] == 350.0

    r2 = client.post(f"/financeiro/cobrancas/{pid}/pix", headers=h)
    assert r2.json()["txid"] == r1.json()["txid"]
    assert mp_falso["criar"] == 1


def test_gera_novo_pix_quando_expirado(mp_falso):
    uid = _usuario("10000000002")
    pid = _pagamento(uid)
    h = _auth("10000000002")
    client.post(f"/financeiro/cobrancas/{pid}/pix", headers=h)

    db = SessionLocal()
    p = db.get(Pagamento, pid)
    p.pix_expira_em = datetime.utcnow() - timedelta(minutes=1)
    db.commit()
    db.close()

    client.post(f"/financeiro/cobrancas/{pid}/pix", headers=h)
    assert mp_falso["criar"] == 2


def test_nao_gera_pix_de_outro_morador(mp_falso):
    uid = _usuario("10000000003")
    _usuario("10000000004")
    pid = _pagamento(uid)
    r = client.post(f"/financeiro/cobrancas/{pid}/pix", headers=_auth("10000000004"))
    assert r.status_code == 404
    assert mp_falso["criar"] == 0


def test_pix_exige_login_e_cobranca_paga_da_409(mp_falso):
    uid = _usuario("10000000005")
    pid = _pagamento(uid, status="PAGO")
    assert client.post(f"/financeiro/cobrancas/{pid}/pix").status_code == 401
    r = client.post(f"/financeiro/cobrancas/{pid}/pix", headers=_auth("10000000005"))
    assert r.status_code == 409


def test_webhook_aprovado_da_baixa(mp_falso, monkeypatch):
    uid = _usuario("10000000006")
    pid = _pagamento(uid)
    monkeypatch.setattr(mp, "consultar_pagamento", lambda i: {
        "status": "approved", "payment_method_id": "pix",
        "external_reference": str(pid), "transaction_amount": 350.0})

    r = client.post("/webhooks/mercadopago?type=payment&data.id=123")
    assert r.status_code == 200 and r.json()["motivo"] == "baixa realizada"

    r = client.get("/financeiro/cobrancas/10000000006", headers=_auth("10000000006"))
    assert r.json()["cobrancas"][0]["status"] == "PAGO"
    assert r.json()["cobrancas"][0]["data_pagamento"] is not None

    # reenvio da mesma notificação é inofensivo
    r = client.post("/webhooks/mercadopago?type=payment&data.id=123")
    assert r.json()["motivo"] == "já estava paga"


def test_webhook_valor_divergente_nao_da_baixa(mp_falso, monkeypatch):
    uid = _usuario("10000000007")
    pid = _pagamento(uid)
    monkeypatch.setattr(mp, "consultar_pagamento", lambda i: {
        "status": "approved", "payment_method_id": "pix",
        "external_reference": str(pid), "transaction_amount": 1.0})
    r = client.post("/webhooks/mercadopago?type=payment&data.id=124")
    assert r.json()["motivo"] == "valor divergente"
    db = SessionLocal()
    assert db.get(Pagamento, pid).status == "PENDENTE"
    db.close()


def test_webhook_pendente_e_outros_tipos_sao_ignorados(mp_falso, monkeypatch):
    monkeypatch.setattr(mp, "consultar_pagamento", lambda i: {"status": "pending"})
    assert client.post("/webhooks/mercadopago?type=payment&data.id=1").json()["status"] == "ignorado"
    assert client.post("/webhooks/mercadopago?type=plan&data.id=1").json()["status"] == "ignorado"


def test_webhook_assinatura(mp_falso, monkeypatch):
    monkeypatch.setenv("MP_WEBHOOK_SECRET", "segredo")
    monkeypatch.setattr(mp, "consultar_pagamento", lambda i: {"status": "pending"})

    # sem assinatura / assinatura errada
    assert client.post("/webhooks/mercadopago?type=payment&data.id=ABC").status_code == 401
    h = {"x-signature": "ts=1,v1=errado", "x-request-id": "r1"}
    assert client.post("/webhooks/mercadopago?type=payment&data.id=ABC", headers=h).status_code == 401

    # assinatura correta (data.id em minúsculas no manifesto)
    v1 = hmac.new(b"segredo", b"id:abc;request-id:r1;ts:1;", hashlib.sha256).hexdigest()
    h = {"x-signature": f"ts=1,v1={v1}", "x-request-id": "r1"}
    assert client.post("/webhooks/mercadopago?type=payment&data.id=ABC", headers=h).status_code == 200


def test_cobrancas_por_cpf_protegido():
    _usuario("10000000008")
    _usuario("10000000009")
    _usuario("10000000010", tipo="SINDICO")

    assert client.get("/financeiro/cobrancas/10000000008").status_code == 401
    assert client.get("/financeiro/cobrancas/10000000008", headers=_auth("10000000009")).status_code == 403
    assert client.get("/financeiro/cobrancas/10000000008", headers=_auth("10000000008")).status_code == 200
    assert client.get("/financeiro/cobrancas/10000000008", headers=_auth("10000000010", "SINDICO")).status_code == 200


def test_dashboard_e_debug_so_sindico():
    assert client.get("/financeiro/dashboard").status_code == 401
    assert client.get("/financeiro/dashboard", headers=_auth("1", "MORADOR")).status_code == 403
    assert client.get("/financeiro/dashboard", headers=_auth("1", "SINDICO")).status_code == 200
    assert client.get("/financeiro/pagamentos/debug", headers=_auth("1", "MORADOR")).status_code == 403
