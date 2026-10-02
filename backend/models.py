from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Integer, Numeric, String, Text, Time, Float, ForeignKey
from backend.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    nascimento = Column(Date, nullable=False)
    senha_hash = Column(String(255), nullable=False)

    tipo = Column(
    Enum("MORADOR", "SINDICO", name="tipo_usuario"),
    nullable=False
)

    ativo = Column(Boolean, nullable=False, default=True)

    # Dados de perfil (editáveis pelo próprio usuário)
    email = Column(String(150), nullable=True)
    telefone = Column(String(30), nullable=True)
    unidade = Column(String(30), nullable=True)

    criado_em = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp()
    )


class Pagamento(Base):
    __tablename__ = "pagamentos"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=True
    )

    descricao = Column(
        String,
        nullable=False
    )

    valor = Column(
        Float,
        nullable=False
    )

    vencimento = Column(
        Date,
        nullable=False
    )

    status = Column(
        String,
        default="PENDENTE",
        nullable=False
    )

    data_pagamento = Column(
        Date,
        nullable=True
    )

    # Pix (Mercado Pago)
    mp_payment_id = Column(String(40), nullable=True)
    pix_copia_e_cola = Column(Text, nullable=True)
    pix_expira_em = Column(DateTime, nullable=True)

    usuario = relationship("Usuario")


class CobrancaRecorrente(Base):
    __tablename__ = "cobrancas_recorrentes"

    id = Column(Integer, primary_key=True, index=True)

    descricao = Column(
        String,
        nullable=False
    )

    valor = Column(
        Float,
        nullable=False
    )

    dia_vencimento = Column(
        Integer,
        nullable=False
    )

    ativo = Column(
        Boolean,
        default=True,
        nullable=False
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



class Aviso(Base):
    __tablename__ = "avisos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(120), nullable=False)
    mensagem = Column(Text, nullable=False)
    prioridade = Column(String(15), nullable=False, default="NORMAL")
    autor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    criado_em = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    autor = relationship("Usuario")


class Chamado(Base):
    """Solicitação de manutenção ou registro de ocorrência feito por um morador."""

    __tablename__ = "chamados"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    tipo = Column(String(15), nullable=False, default="MANUTENCAO")  # MANUTENCAO | OCORRENCIA
    categoria = Column(String(40), nullable=False)
    titulo = Column(String(120), nullable=False)
    descricao = Column(Text, nullable=False)
    local = Column(String(100), nullable=True)
    prioridade = Column(String(10), nullable=False, default="MEDIA")  # BAIXA | MEDIA | ALTA
    status = Column(String(20), nullable=False, default="ABERTO")  # ABERTO | EM_ANDAMENTO | CONCLUIDO
    resposta = Column(Text, nullable=True)
    criado_em = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    atualizado_em = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    usuario = relationship("Usuario")


class Condominio(Base):
    """Dados do condomínio (uma única linha, id=1)."""

    __tablename__ = "condominio"

    id = Column(Integer, primary_key=True)
    nome = Column(String(150), nullable=False, default="Meu Condomínio")
    endereco = Column(String(200), nullable=True)
    telefone = Column(String(30), nullable=True)
    email = Column(String(150), nullable=True)
    regras = Column(Text, nullable=True)
