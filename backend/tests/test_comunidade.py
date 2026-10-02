import os
from datetime import date

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_pix.db")
os.environ.setdefault("RESET_DATABASE", "true")

from fastapi.testclient import TestClient

from backend.auth import criar_token, gerar_hash
from backend.database import SessionLocal
from backend.main import app
from backend.models import Usuario

client = TestClient(app)


def _usuario(cpf, tipo="MORADOR", senha="abc123"):
    db = SessionLocal()
    db.add(Usuario(nome=f"Pessoa {cpf}", cpf=cpf, nascimento=date(1990, 5, 5),
                   senha_hash=gerar_hash(senha), tipo=tipo))
    db.commit()
    db.close()
    return {"Authorization": f"Bearer {criar_token({'sub': cpf, 'tipo': tipo})}"}


def test_perfil_ler_e_editar():
    h = _usuario("20000000001")
    r = client.get("/perfil", headers=h)
    assert r.status_code == 200 and r.json()["cpf"] == "20000000001"

    r = client.put("/perfil", headers=h, json={"unidade": "Apto 12", "telefone": "11999990000",
                                                "email": "a@b.com"})
    assert r.status_code == 200
    assert r.json()["unidade"] == "Apto 12" and r.json()["email"] == "a@b.com"

    assert client.put("/perfil", headers=h, json={"email": "invalido"}).status_code == 400
    assert client.get("/perfil").status_code == 401


def test_alterar_senha():
    h = _usuario("20000000002")
    assert client.post("/perfil/senha", headers=h,
                       json={"senha_atual": "errada", "nova_senha": "novasenha"}).status_code == 400
    assert client.post("/perfil/senha", headers=h,
                       json={"senha_atual": "abc123", "nova_senha": "123"}).status_code == 422
    assert client.post("/perfil/senha", headers=h,
                       json={"senha_atual": "abc123", "nova_senha": "novasenha"}).status_code == 200
    r = client.post("/login", json={"cpf": "20000000002", "senha": "novasenha"})
    assert r.json()["status"] == "ok"


def test_avisos_sindico_publica_morador_le():
    s = _usuario("20000000003", "SINDICO")
    m = _usuario("20000000004")

    corpo = {"titulo": "Caixa d'água", "mensagem": "Limpeza dia 10.", "prioridade": "IMPORTANTE"}
    assert client.post("/avisos", headers=m, json=corpo).status_code == 403
    r = client.post("/avisos", headers=s, json=corpo)
    assert r.status_code == 201
    aviso_id = r.json()["id"]
    assert r.json()["autor"] == "Pessoa 20000000003"

    lista = client.get("/avisos", headers=m).json()
    assert any(a["id"] == aviso_id for a in lista)

    assert client.delete(f"/avisos/{aviso_id}", headers=m).status_code == 403
    assert client.delete(f"/avisos/{aviso_id}", headers=s).status_code == 200
    assert client.delete(f"/avisos/{aviso_id}", headers=s).status_code == 404


def test_chamados_fluxo_completo():
    s = _usuario("20000000005", "SINDICO")
    m1 = _usuario("20000000006")
    m2 = _usuario("20000000007")

    r = client.post("/chamados", headers=m1, json={
        "tipo": "MANUTENCAO", "categoria": "Elétrica", "titulo": "Lâmpada queimada",
        "descricao": "Corredor do 2º andar sem luz.", "prioridade": "ALTA"})
    assert r.status_code == 201 and r.json()["status"] == "ABERTO"
    cid = r.json()["id"]

    client.post("/chamados", headers=m2, json={
        "tipo": "OCORRENCIA", "categoria": "Barulho", "titulo": "Som alto",
        "descricao": "Música alta depois das 22h."})

    # morador vê só os seus
    meus = client.get("/chamados/meus", headers=m1).json()
    assert [c["id"] for c in meus] == [cid]

    # morador não acessa a lista geral nem atualiza
    assert client.get("/chamados", headers=m1).status_code == 403
    assert client.patch(f"/chamados/{cid}", headers=m1, json={"status": "CONCLUIDO"}).status_code == 403

    # síndico filtra e atualiza
    ocorrencias = client.get("/chamados?tipo=OCORRENCIA", headers=s).json()
    assert ocorrencias and all(c["tipo"] == "OCORRENCIA" for c in ocorrencias)

    r = client.patch(f"/chamados/{cid}", headers=s,
                     json={"status": "EM_ANDAMENTO", "resposta": "Eletricista agendado."})
    assert r.status_code == 200
    assert r.json()["status"] == "EM_ANDAMENTO" and r.json()["resposta"] == "Eletricista agendado."
    assert client.patch(f"/chamados/{cid}", headers=s, json={"status": "XYZ"}).status_code == 422

    resumo = client.get("/chamados/resumo", headers=s).json()
    assert resumo["manutencoes_abertas"] >= 1 and resumo["ocorrencias_abertas"] >= 1


def test_condominio_e_lista_de_moradores():
    s = _usuario("20000000008", "SINDICO")
    m = _usuario("20000000009")

    assert client.get("/condominio", headers=m).json()["nome"]
    assert client.put("/condominio", headers=m, json={"nome": "X"}).status_code == 403
    r = client.put("/condominio", headers=s, json={"nome": "Residencial Sol", "telefone": "1133334444"})
    assert r.status_code == 200 and r.json()["nome"] == "Residencial Sol"

    assert client.get("/moradores", headers=m).status_code == 403
    assert client.get("/moradores", headers=s).status_code == 200
    assert client.get("/moradores").status_code == 401
