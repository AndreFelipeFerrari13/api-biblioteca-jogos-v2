from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Definição dos campos conforme a especificação [cite: 27, 28, 29, 30]
class JogoBase(BaseModel):
    nome: str
    tipo: str
    nota: int
    review: str

class JogoResponse(JogoBase):
    id: int

# Banco de dados inicial conforme o exemplo do PDF [cite: 25, 32]
banco_jogos = [
    {"id": 1, "nome": "The Legend of Zelda", "tipo": "Aventura", "nota": 10, "review": "Um clássico absoluto."},
    {"id": 2, "nome": "FIFA 23", "tipo": "Esporte", "nota": 7, "review": "Bom para jogar com amigos."}
]

# --- ENDPOINTS ---

# POST /login [cite: 14]
@app.post("/login")
def login(dados: dict):
    # Regra exata de e-mail e senha [cite: 16]
    if dados.get("email") == "usuario@esoft.com" and dados.get("password") == "Abc123":
        return {"token": "550e8400-e29b-41d4-a716-446655440000"} # UUID exigido [cite: 20]
    raise HTTPException(status_code=401, detail="Credenciais incorretas")

# GET /jogos [cite: 21]
@app.get("/jogos", response_model=List[JogoResponse])
def listar_jogos():
    return banco_jogos

# GET /jogos/{id} [cite: 40]
@app.get("/jogos/{id}", response_model=JogoResponse)
def buscar_jogo(id: int):
    for jogo in banco_jogos:
        if jogo["id"] == id:
            return jogo
    raise HTTPException(status_code=404, detail="Jogo não encontrado")

# POST /jogos [cite: 50]
@app.post("/jogos", status_code=status.HTTP_201_CREATED, response_model=JogoResponse)
def criar_jogo(jogo: JogoBase):
    # Gera um novo ID sequencial
    novo_id = max([j["id"] for j in banco_jogos]) + 1 if banco_jogos else 1
    item = jogo.dict()
    item["id"] = novo_id
    banco_jogos.append(item)
    return item

# PUT /jogos/{id} [cite: 67]
@app.put("/jogos/{id}", response_model=JogoResponse)
def atualizar_jogo(id: int, jogo_atualizado: JogoBase):
    for index, jogo in enumerate(banco_jogos):
        if jogo["id"] == id:
            item = jogo_atualizado.dict()
            item["id"] = id
            banco_jogos[index] = item
            return item
    raise HTTPException(status_code=404, detail="Jogo não encontrado")

# DELETE /jogos/{id} [cite: 84]
@app.delete("/jogos/{id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_jogo(id: int):
    for index, jogo in enumerate(banco_jogos):
        if jogo["id"] == id:
            banco_jogos.pop(index)
            return None # Sem corpo de resposta conforme [cite: 86]
    raise HTTPException(status_code=404, detail="Jogo não encontrado")