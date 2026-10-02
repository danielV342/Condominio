from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import sindico_atual, usuario_atual
from backend.models import Condominio, Usuario

router = APIRouter()


class CondominioUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    endereco: str | None = Field(default=None, max_length=200)
    telefone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    regras: str | None = Field(default=None, max_length=4000)


def _obter(db: Session) -> Condominio:
    cond = db.query(Condominio).filter(Condominio.id == 1).first()
    if not cond:
        cond = Condominio(id=1, nome="Meu Condomínio")
        db.add(cond)
        db.commit()
        db.refresh(cond)
    return cond


def _dados(c: Condominio) -> dict:
    return {
        "nome": c.nome,
        "endereco": c.endereco,
        "telefone": c.telefone,
        "email": c.email,
        "regras": c.regras,
    }


@router.get("/condominio")
def obter_condominio(
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    return _dados(_obter(db))


@router.put("/condominio")
def atualizar_condominio(
    dados: CondominioUpdate,
    sindico: Usuario = Depends(sindico_atual),
    db: Session = Depends(get_db),
):
    cond = _obter(db)
    for campo in ("endereco", "telefone", "email", "regras"):
        valor = getattr(dados, campo)
        if valor is not None:
            setattr(cond, campo, valor.strip() or None)
    if dados.nome is not None:
        cond.nome = dados.nome.strip()
    db.commit()
    db.refresh(cond)
    return _dados(cond)
