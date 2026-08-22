from fastapi import Header, HTTPException
from backend.auth import verificar_token

# VALIDAR USUÁRIO LOGADO

def usuario_logado(authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Token não enviado"
        )

    try:
        token = authorization.split(" ")[1]

    except:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    dados = verificar_token(token)

    if not dados:
        raise HTTPException(
            status_code=401,
            detail="Token expirado ou inválido"
        )

    return dados