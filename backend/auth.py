from datetime import datetime, timedelta, UTC

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


SECRET_KEY = "condominio"
ALGORITHM = "HS256"

security = HTTPBearer()



def gerar_hash(senha: str):
    return pwd_context.hash(senha)



def verificar_senha(senha: str, hash_senha: str):
    return pwd_context.verify(senha, hash_senha)



def criar_token(dados: dict):

    dados_copy = dados.copy()

    expire = datetime.now(UTC) + timedelta(hours=24)

    dados_copy.update({
        "exp": expire
    })

    token = jwt.encode(
        dados_copy,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token



def validar_token(
    credenciais: HTTPAuthorizationCredentials = Depends(security)
):

    token = credenciais.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )