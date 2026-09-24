from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Integer, Numeric, String, Time
from backend.database import Base
from sqlalchemy.sql import func


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    nascimento = Column(Date, nullable=False)
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
    mensagem = Column(String(500), nullable=False)
    data = Column(DateTime, nullable=False, server_default=func.current_timestamp())


class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True)
    nome = Column(String(150), nullable=False)
    data = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    status = Column(String(20), nullable=False, default="pendente")


class Pagamento(Base):
    __tablename__ = "pagamentos"

    id = Column(Integer, primary_key=True)
    valor = Column(Numeric(10, 2), nullable=False)