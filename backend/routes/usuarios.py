from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends

from backend.auth import gerar_hash, verificar_senha, criar_token
from backend.database import get_db
from backend.database import SessionLocal
from backend.models import Usuario
from backend.schemas import UsuarioCreate, LoginSchema

router = APIRouter()


@router.post("/cadastro")
def cadastrar(usuario: UsuarioCreate):

    db: Session = SessionLocal()

    existe = db.query(Usuario).filter(
        Usuario.cpf == usuario.cpf
    ).first()

    if existe:
        return {
            "status": "erro",
            "mensagem": "CPF já cadastrado"
        }

    novo = Usuario(
        nome=usuario.nome,
        cpf=usuario.cpf,
        nascimento=usuario.nascimento,
        senha=gerar_hash(usuario.senha),
        tipo=usuario.tipo
    )

    db.add(novo)
    db.commit()

    return {"status": "ok"}

@router.post("/")
def login(dados: LoginSchema):

    db: Session = SessionLocal()

    usuario = db.query(Usuario).filter(
        Usuario.cpf == dados.cpf
    ).first()

    if not usuario:
        return {"status": "erro"}

    senha_ok = verificar_senha(
        dados.senha,
        usuario.senha
    )

    if not senha_ok:
        return {"status": "erro"}

    token = criar_token({
        "sub": usuario.cpf,
        "nome": usuario.nome,
        "tipo": usuario.tipo
    })

    return {
        "status": "ok",
        "token": token,
        "nome": usuario.nome,
        "cpf": usuario.cpf,
        "tipo": usuario.tipo
    }