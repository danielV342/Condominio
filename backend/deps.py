from fastapi import Depends, Header, HTTPException

from backend.auth import verificar_token


def usuario_logado(authorization: str | None = Header(default=None)):
    """Retorna os dados do usuário presentes no JWT do header Authorization."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não enviado")

    partes = authorization.split(" ", 1)
    if len(partes) != 2 or partes[0].lower() != "bearer" or not partes[1].strip():
        raise HTTPException(status_code=401, detail="Token inválido")

    dados = verificar_token(partes[1].strip())
    if not dados:
        raise HTTPException(status_code=401, detail="Token expirado ou inválido")

    return dados



def apenas_sindico(usuario=Depends(usuario_logado)):
    """Exige um JWT de síndico."""
    if str(usuario.get("tipo", "")).upper() != "SINDICO":
        raise HTTPException(status_code=403, detail="Acesso restrito ao síndico.")
    return usuario
