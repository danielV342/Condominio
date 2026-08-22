from fastapi import APIRouter
from fastapi import Depends
from backend.auth import validar_token

router = APIRouter()


reservas_db = [
]


@router.get("/reservas")
def listar(usuario = Depends(validar_token)):

    return reservas_db


@router.post("/reservas")
def criar_reserva(reserva: dict):

    for r in reservas_db:

        mesmo_tipo = r[2] == reserva["tipo"]
        mesma_data = r[3] == reserva["data"]
        mesma_hora = r[4] == reserva["hora"]

        status_ativo = r[5] != "recusado"

        if mesmo_tipo and mesma_data and mesma_hora and status_ativo:

            return {
                "status": "erro",
                "mensagem": "Horário já reservado para este local!"
            }

    nova = [
        len(reservas_db) + 1,
        reserva["nome"],
        reserva["tipo"],
        reserva["data"],
        reserva["hora"],
        "pendente"
    ]

    reservas_db.append(nova)

    return {
        "status":"ok"
    }

@router.post("/reservas/aprovar")
def aprovar(
    data: dict,
    usuario = Depends(validar_token)
):

    id_reserva = data["id"]

    for r in reservas_db:
        if r[0] == id_reserva:
            r[5] = "aprovado"

    return {"status":"ok"}


@router.post("/reservas/recusar")
def recusar(data: dict):

    id_reserva = data["id"]

    for r in reservas_db:
        if r[0] == id_reserva:
            r[5] = "recusado"

    return {"status":"ok"}