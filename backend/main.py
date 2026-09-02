from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.routes import usuarios
from backend.routes import mural
from backend.routes import reservas
from backend.routes import pagamentos

app = FastAPI(title="API Condomínio")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ROTAS
app.include_router(usuarios.router)
app.include_router(mural.router)
app.include_router(reservas.router)
app.include_router(pagamentos.router)


@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/cadastro.html")
def cadastro():
    return FileResponse("cadastro.html")

@app.get("/dashboard.html")
def dashboard():
    return FileResponse("dashboard.html")