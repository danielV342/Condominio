from pydantic import BaseModel
from datetime import date

class UsuarioCreate(BaseModel):
    nome: str
    cpf: str
    nascimento: str
    senha: str
    tipo: str = "morador"

class LoginSchema(BaseModel):
    cpf: str
    senha: str

class MuralSchema(BaseModel):
    mensagem: str

class ReservaSchema(BaseModel):
    nome: str
    data: str
    hora: str

class PagamentoResponse(BaseModel):

    id: int
    descricao: str
    valor: float
    vencimento: date
    status: str
    data_pagamento: date | None