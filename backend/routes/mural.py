from fastapi import APIRouter

router = APIRouter()

mural_db = [
    [1, "Aviso teste", "16/05/2026"]
]

@router.get("/mural")
def mural():
    return mural_db

@router.post("/mural")
def postar(data: dict):

    novo = [
        len(mural_db)+1,
        data["mensagem"],
        "hoje"
    ]

    mural_db.append(novo)

    return {"status":"ok"}

@router.post("/mural/deletar")
def deletar(data: dict):

    id_msg = data["id"]

    global mural_db

    mural_db = [m for m in mural_db if m[0] != id_msg]

    return {"status":"ok"}