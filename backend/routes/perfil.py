from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth import gerar_hash, verificar_senha
from backend.database import get_db
from backend.deps import usuario_atual
from backend.models import Usuario

router = APIRouter()


class PerfilUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=3, max_length=150)
    email: str | None = Field(default=None, max_length=150)
    telefone: str | None = Field(default=None, max_length=30)
    unidade: str | None = Field(default=None, max_length=30)


class SenhaUpdate(BaseModel):
    senha_atual: str
    nova_senha: str = Field(min_length=6, max_length=72)


def _perfil(u: Usuario) -> dict:
    return {
        "id": u.id,
        "nome": u.nome,
        "cpf": u.cpf,
        "nascimento": u.nascimento,
        "tipo": u.tipo,
        "email": u.email,
        "telefone": u.telefone,
        "unidade": u.unidade,
    }


@router.get("/perfil")
def obter_perfil(usuario: Usuario = Depends(usuario_atual)):
    return _perfil(usuario)


@router.put("/perfil")
def atualizar_perfil(
    dados: PerfilUpdate,
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    # Só altera o que foi enviado; string vazia limpa o campo (exceto nome).
    for campo in ("email", "telefone", "unidade"):
        valor = getattr(dados, campo)
        if valor is not None:
            setattr(usuario, campo, valor.strip() or None)

    if dados.nome is not None:
        usuario.nome = dados.nome.strip()

    if usuario.email and ("@" not in usuario.email or "." not in usuario.email):
        raise HTTPException(status_code=400, detail="Informe um e-mail válido.")

    db.commit()
    db.refresh(usuario)
    return _perfil(usuario)


@router.post("/perfil/senha")
def alterar_senha(
    dados: SenhaUpdate,
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    if not verificar_senha(dados.senha_atual, usuario.senha_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")

    if dados.senha_atual == dados.nova_senha:
        raise HTTPException(status_code=400, detail="A nova senha deve ser diferente da atual.")

    usuario.senha_hash = gerar_hash(dados.nova_senha)
    db.commit()
    return {"status": "ok"}
