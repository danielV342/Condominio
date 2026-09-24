from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from backend.database import Base
from sqlalchemy.sql import func


from database import Base
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)

    tipo = Column(
        Enum("MORADOR", "SINDICO"),
        nullable=False
    )

    ativo = Column(Boolean, nullable=False, default=True)

    criado_em = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp()
    )

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