from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_home():

    response = client.get("/")

    assert response.status_code == 200

def test_login():

    # CADASTRA USUÁRIO
    client.post("/cadastro", json={
        "nome":"Teste",
        "cpf":"123",
        "nascimento":"2000-01-01",
        "senha":"1234"
    })

    # FAZ LOGIN
    response = client.post("/login", json={
        "cpf":"123",
        "senha":"1234"
    })

    assert response.status_code == 200

    dados = response.json()

    assert "token" in dados

def test_cadastro():

    response = client.post("/cadastro", json={
        "nome":"Teste",
        "cpf":"123",
        "nascimento":"2000-01-01",
        "senha":"1234"
    })

    assert response.status_code == 200

def test_login_invalido():

    response = client.post("/login", json={
        "cpf":"999",
        "senha":"errada"
    })

    dados = response.json()

    assert dados["status"] == "erro"

def test_reserva():

    # cadastro
    client.post("/cadastro", json={
        "nome":"Teste",
        "cpf":"111",
        "nascimento":"2000-01-01",
        "senha":"1234"
    })

    # login
    login = client.post("/login", json={
        "cpf":"111",
        "senha":"1234"
    })

    token = login.json()["token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # reserva
    response = client.post(
        "/reservas",
        headers=headers,
        json={
            "nome":"Dickson",
            "tipo":"Piscina",
            "data":"2026-05-20",
            "hora":"08:00"
        }
    )

    assert response.status_code == 200

def test_listar_reservas():

    # cadastro
    client.post("/cadastro", json={
        "nome":"Teste",
        "cpf":"222",
        "nascimento":"2000-01-01",
        "senha":"1234"
    })

    # login
    login = client.post("/login", json={
        "cpf":"222",
        "senha":"1234"
    })

    token = login.json()["token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(
        "/reservas",
        headers=headers
    )

    assert response.status_code == 200

def test_pagamento():

    response = client.get("/pagamento")

    assert response.status_code == 200

def test_reserva_com_token():

    # cadastro
    client.post("/cadastro", json={
        "nome":"Teste",
        "cpf":"777",
        "nascimento":"2000-01-01",
        "senha":"1234"
    })

    # login
    login = client.post("/login", json={
        "cpf":"777",
        "senha":"1234"
    })

    token = login.json()["token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(
        "/reservas",
        headers=headers
    )

    assert response.status_code == 200

def test_reserva_sem_token():

    response = client.get("/reservas")

    assert response.status_code == 401


