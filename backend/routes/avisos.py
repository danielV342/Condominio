from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import sindico_atual, usuario_atual
from backend.models import Aviso, Usuario

router = APIRouter()


class AvisoCreate(BaseModel):
    titulo: str = Field(min_length=3, max_length=120)
    mensagem: str = Field(min_length=3, max_length=2000)
    prioridade: Literal["NORMAL", "IMPORTANTE", "URGENTE"] = "NORMAL"


def _aviso(a: Aviso) -> dict:
    return {
        "id": a.id,
        "titulo": a.titulo,
        "mensagem": a.mensagem,
        "prioridade": a.prioridade,
        "autor": a.autor.nome if a.autor else None,
        "criado_em": a.criado_em,
    }


@router.get("/avisos")
def listar_avisos(
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    avisos = db.query(Aviso).order_by(Aviso.criado_em.desc(), Aviso.id.desc()).all()
    return [_aviso(a) for a in avisos]


@router.post("/avisos", status_code=201)
def criar_aviso(
    dados: AvisoCreate,
    sindico: Usuario = Depends(sindico_atual),
    db: Session = Depends(get_db),
):
    aviso = Aviso(
        titulo=dados.titulo.strip(),
        mensagem=dados.mensagem.strip(),
        prioridade=dados.prioridade,
        autor_id=sindico.id,
    )
    db.add(aviso)
    db.commit()
    db.refresh(aviso)
    return _aviso(aviso)


@router.delete("/avisos/{aviso_id}")
def apagar_aviso(
    aviso_id: int,
    sindico: Usuario = Depends(sindico_atual),
    db: Session = Depends(get_db),
):
    aviso = db.query(Aviso).filter(Aviso.id == aviso_id).first()
    if not aviso:
        raise HTTPException(status_code=404, detail="Aviso não encontrado.")
    db.delete(aviso)
    db.commit()
    return {"status": "ok"}
