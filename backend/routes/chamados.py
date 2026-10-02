from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import sindico_atual, usuario_atual
from backend.models import Chamado, Usuario

router = APIRouter()

Tipo = Literal["MANUTENCAO", "OCORRENCIA"]
Prioridade = Literal["BAIXA", "MEDIA", "ALTA"]
Status = Literal["ABERTO", "EM_ANDAMENTO", "CONCLUIDO"]


class ChamadoCreate(BaseModel):
    tipo: Tipo = "MANUTENCAO"
    categoria: str = Field(min_length=2, max_length=40)
    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=5, max_length=2000)
    local: str | None = Field(default=None, max_length=100)
    prioridade: Prioridade = "MEDIA"


class ChamadoUpdate(BaseModel):
    status: Status | None = None
    resposta: str | None = Field(default=None, max_length=2000)


def _chamado(c: Chamado) -> dict:
    return {
        "id": c.id,
        "tipo": c.tipo,
        "categoria": c.categoria,
        "titulo": c.titulo,
        "descricao": c.descricao,
        "local": c.local,
        "prioridade": c.prioridade,
        "status": c.status,
        "resposta": c.resposta,
        "criado_em": c.criado_em,
        "atualizado_em": c.atualizado_em,
        "morador": c.usuario.nome if c.usuario else None,
        "unidade": c.usuario.unidade if c.usuario else None,
    }


def _agora() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@router.post("/chamados", status_code=201)
def criar_chamado(
    dados: ChamadoCreate,
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    chamado = Chamado(
        usuario_id=usuario.id,
        tipo=dados.tipo,
        categoria=dados.categoria.strip(),
        titulo=dados.titulo.strip(),
        descricao=dados.descricao.strip(),
        local=(dados.local or "").strip() or None,
        prioridade=dados.prioridade,
        status="ABERTO",
        criado_em=_agora(),
        atualizado_em=_agora(),
    )
    db.add(chamado)
    db.commit()
    db.refresh(chamado)
    return _chamado(chamado)


@router.get("/chamados/meus")
def meus_chamados(
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    itens = (
        db.query(Chamado)
        .filter(Chamado.usuario_id == usuario.id)
        .order_by(Chamado.criado_em.desc(), Chamado.id.desc())
        .all()
    )
    return [_chamado(c) for c in itens]


@router.get("/chamados/resumo")
def resumo_chamados(
    sindico: Usuario = Depends(sindico_atual),
    db: Session = Depends(get_db),
):
    abertos = db.query(Chamado).filter(Chamado.status != "CONCLUIDO").all()
    return {
        "manutencoes_abertas": sum(1 for c in abertos if c.tipo == "MANUTENCAO"),
        "ocorrencias_abertas": sum(1 for c in abertos if c.tipo == "OCORRENCIA"),
    }


@router.get("/chamados")
def listar_chamados(
    tipo: Tipo | None = None,
    status: Status | None = None,
    sindico: Usuario = Depends(sindico_atual),
    db: Session = Depends(get_db),
):
    consulta = db.query(Chamado)
    if tipo:
        consulta = consulta.filter(Chamado.tipo == tipo)
    if status:
        consulta = consulta.filter(Chamado.status == status)
    itens = consulta.order_by(Chamado.criado_em.desc(), Chamado.id.desc()).all()
    return [_chamado(c) for c in itens]


@router.patch("/chamados/{chamado_id}")
def atualizar_chamado(
    chamado_id: int,
    dados: ChamadoUpdate,
    sindico: Usuario = Depends(sindico_atual),
    db: Session = Depends(get_db),
):
    chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado.")

    if dados.status is not None:
        chamado.status = dados.status
    if dados.resposta is not None:
        chamado.resposta = dados.resposta.strip() or None

    chamado.atualizado_em = _agora()
    db.commit()
    db.refresh(chamado)
    return _chamado(chamado)
