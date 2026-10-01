import os
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Use a secret from Render/environment when available. The fallback keeps local
# development working, but production should always define SECRET_KEY.
SECRET_KEY = os.getenv("SECRET_KEY", "condominio-dev-secret-change-me")
ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = 24

security = HTTPBearer()


def gerar_hash(senha: str) -> str:
    return pwd_context.hash(senha)


def verificar_senha(senha: str, hash_senha: str) -> bool:
    return pwd_context.verify(senha, hash_senha)


def criar_token(dados: dict) -> str:
    dados_copy = dados.copy()
    dados_copy["exp"] = datetime.now(UTC) + timedelta(hours=TOKEN_EXPIRATION_HOURS)

    return jwt.encode(
        dados_copy,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def verificar_token(token: str) -> dict:
    """Valida um JWT e retorna seu payload.

    Esta função é usada por backend.deps.usuario_logado. Ela não depende
    de FastAPI/Depends, portanto também pode ser usada diretamente em testes.
    """
    if not token:
        return {}

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except (JWTError, ValueError, TypeError):
        return {}


def validar_token(
    credenciais: HTTPAuthorizationCredentials = Depends(security),
):
    payload = verificar_token(credenciais.credentials)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado",
        )

    return payload
