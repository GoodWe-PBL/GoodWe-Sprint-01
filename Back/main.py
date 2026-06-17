from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()
sessions = []
chargers = [
    {
        "id": 1,
        "nome": "Carregador Principal",
        "status": "livre"
    }
]

# Banco fake temporário
users = []

class UserRegister(BaseModel):
    nome: str
    email: str
    senha: str
    tipo: str = "morador"

class UserLogin(BaseModel):
    email: str
    senha: str
    
class SessionCreate(BaseModel):
    usuario_email: str
    carregador_id: int
    energia_kwh: float


@app.get("/")
def home():
    return {"status": "online"}


@app.post("/register")
def register(user: UserRegister):

    # Verifica email repetido
    for existing_user in users:
        if existing_user["email"] == user.email:
            raise HTTPException(
                status_code=400,
                detail="Email já cadastrado"
            )

    users.append({
        "nome": user.nome,
        "email": user.email,
        "senha": user.senha,
        "tipo": user.tipo
    })

    return {
        "message": "Usuário cadastrado com sucesso"
    }


@app.post("/login")
def login(user: UserLogin):

    for existing_user in users:

        if (
            existing_user["email"] == user.email
            and existing_user["senha"] == user.senha
        ):
            return {
                "message": "Login realizado",
                "usuario": existing_user["nome"]
            }

    raise HTTPException(
        status_code=401,
        detail="Email ou senha inválidos"
    )

@app.get("/users")
def list_users():
    return users

@app.get("/chargers")
def list_chargers():
    return chargers

@app.get("/sessions")
def list_sessions():
    return sessions

@app.post("/sessions")
def create_session(session: SessionCreate):

    # verifica se carregador existe
    charger = next((c for c in chargers if c["id"] == session.carregador_id), None)
    if not charger:
        raise HTTPException(status_code=404, detail="Carregador não encontrado")

    # verifica status do carregador
    if charger.get("status") != "livre":
        raise HTTPException(status_code=400, detail="Carregador ocupado")

    # verifica se usuário existe
    usuario = next((u for u in users if u["email"] == session.usuario_email), None)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # cria sessão e atualiza status do carregador
    new_session = {
    "id": len(sessions) + 1,
    "usuario": usuario["nome"],
    "usuario_email": usuario["email"],
    "carregador_id": charger["id"],
    "energia_kwh": session.energia_kwh,
    "status": "ativa",
    "inicio": datetime.now().isoformat()
}
    sessions.append(new_session)
    charger["status"] = "ocupado"



    return {"message": "Sessão criada", "session": new_session} 

@app.post("/sessions/{session_id}/finish")
def finish_session(session_id: int):    

    session = next((s for s in sessions if s["id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    if session["status"] != "ativa":
        raise HTTPException(status_code=400, detail="Sessão já finalizada")

    session["status"] = "finalizada"

    # libera o carregador
    charger = next((c for c in chargers if c["id"] == session["carregador_id"]), None)
    if charger:
        charger["status"] = "livre"

    return {"message": "Sessão finalizada", "session": session}