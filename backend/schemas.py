from pydantic import BaseModel

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

class PagamentoSchema(BaseModel):
    valor: str