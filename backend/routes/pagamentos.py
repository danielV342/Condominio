from fastapi import APIRouter

router = APIRouter()

valor = 100

@router.get("/pagamento")
def pagamento():
    return {"valor": valor}

@router.post("/pagamento")
def atualizar(data: dict):

    global valor

    valor = float(data["valor"])

    return {"status":"ok"}