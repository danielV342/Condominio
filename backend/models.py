from sqlalchemy import Column, Integer, String
from backend.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    cpf = Column(String)
    nascimento = Column(String)
    senha = Column(String)
    tipo = Column(String, default="morador")

class Mural(Base):
    __tablename__ = "mural"

    id = Column(Integer, primary_key=True)
    mensagem = Column(String)
    data = Column(String)

class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True)
    nome = Column(String)
    data = Column(String)
    hora = Column(String)
    status = Column(String, default="pendente")

class Pagamento(Base):
    __tablename__ = "pagamentos"

    id = Column(Integer, primary_key=True)
    valor = Column(String)