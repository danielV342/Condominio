from fastapi import Depends, Header, HTTPException

from sqlalchemy.orm import Session

from backend.auth import verificar_token
from backend.database import get_db
from backend.models import Usuario


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


def usuario_atual(
    token=Depends(usuario_logado),
    db: Session = Depends(get_db),
) -> Usuario:
    """Carrega do banco o usuário dono do JWT."""
    usuario = db.query(Usuario).filter(Usuario.cpf == token.get("sub")).first()
    if not usuario or not usuario.ativo:
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou inativo")
    return usuario


def sindico_atual(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
    if str(usuario.tipo).upper() != "SINDICO":
        raise HTTPException(status_code=403, detail="Acesso restrito ao síndico.")
    return usuario
