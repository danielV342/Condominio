from sqlalchemy import text

from backend.database import engine

print("Testando SQLAlchemy...")

try:
    with engine.connect() as connection:
        resultado = connection.execute(text("SELECT VERSION()"))
        print("SQLAlchemy conectado!")
        print("Banco:", resultado.fetchone()[0])

except Exception as erro:
    print("Erro:")
    print(type(erro).__name__)
    print(erro)