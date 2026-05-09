from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field, validator
from typing import List

app = FastAPI(
    title="Biblioteca de Jogos API",
    version="1.0.0"
)

# ==================== AUTENTICAÇÃO ====================

TOKEN_VALIDO = "550e8400-e29b-41d4-a716-446655440000"
security = HTTPBearer()

def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail={
                "status": "erro",
                "mensagem": "Formato de autenticação inválido. Use: Authorization: Bearer <token>"
            }
        )
    if credentials.credentials != TOKEN_VALIDO:
        raise HTTPException(
            status_code=401,
            detail={
                "status": "erro",
                "mensagem": "Token inválido ou expirado. Faça login em POST /login para obter um token."
            }
        )

# ==================== MODELS ====================

class LoginRequest(BaseModel):
    email: str
    password: str

class JogoBase(BaseModel):
    nome: str = Field(..., min_length=1)
    tipo: str = Field(..., min_length=1)
    nota: int = Field(..., ge=0, le=10)
    review: str = Field(..., min_length=1)

    @validator("nome", "tipo", "review")
    def sem_espacos_em_branco(cls, v, field):
        if v.strip() == "":
            raise ValueError(f"O campo '{field.name}' não pode ser apenas espaços em branco")
        return v.strip()

class JogoResponse(JogoBase):
    id: int

# ==================== BANCO DE DADOS ====================

banco_jogos: List[dict] = [
    {"id": 1, "nome": "The Legend of Zelda", "tipo": "Aventura", "nota": 10, "review": "Um clássico absoluto."},
    {"id": 2, "nome": "FIFA 23", "tipo": "Esporte", "nota": 7, "review": "Bom para jogar com amigos."}
]

proximo_id = 3

# ==================== HANDLERS GLOBAIS DE ERRO ====================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401:
        return JSONResponse(
            status_code=401,
            content={
                "status": "erro",
                "mensagem": "Não autenticado. Envie o header: Authorization: Bearer <token>"
            }
        )
    if exc.status_code == 403:
        return JSONResponse(
            status_code=403,
            content={
                "status": "erro",
                "mensagem": "Acesso negado. Você não tem permissão para acessar este recurso."
            }
        )
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "status": "erro",
                "mensagem": "Rota não encontrada. Verifique a URL e tente novamente."
            }
        )
    if exc.status_code == 405:
        return JSONResponse(
            status_code=405,
            content={
                "status": "erro",
                "mensagem": "Método HTTP não permitido para esta rota."
            }
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "erro", "mensagem": str(exc.detail)}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    erros = []
    for error in exc.errors():
        campo = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
        erros.append({
            "campo": campo if campo else "body",
            "erro": error["msg"],
            "valor_recebido": str(error.get("input", "não informado"))
        })
    return JSONResponse(
        status_code=422,
        content={
            "status": "erro",
            "mensagem": "Dados inválidos na requisição. Verifique os campos abaixo.",
            "detalhes": erros
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": "erro",
            "mensagem": "Erro interno no servidor.",
            "detalhe": str(exc)
        }
    )

# ==================== ENDPOINTS ====================

@app.post("/login", tags=["Auth"])
def login(dados: LoginRequest):
    if dados.email != "usuario@esoft.com" or dados.password != "Abc123":
        raise HTTPException(
            status_code=401,
            detail={
                "status": "erro",
                "mensagem": "Credenciais incorretas. Verifique o e-mail e a senha informados."
            }
        )
    return {"token": TOKEN_VALIDO}


@app.get("/jogos", response_model=List[JogoResponse], tags=["Jogos"],
         dependencies=[Depends(verificar_token)])
def listar_jogos():
    if not banco_jogos:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "erro",
                "mensagem": "Nenhum jogo cadastrado no momento."
            }
        )
    return banco_jogos


@app.get("/jogos/{id}", response_model=JogoResponse, tags=["Jogos"],
         dependencies=[Depends(verificar_token)])
def buscar_jogo(id: int):
    if id <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "erro",
                "mensagem": f"ID inválido: '{id}'. O ID deve ser um número inteiro positivo."
            }
        )
    for jogo in banco_jogos:
        if jogo["id"] == id:
            return jogo
    raise HTTPException(
        status_code=404,
        detail={
            "status": "erro",
            "mensagem": f"Jogo com ID {id} não encontrado. Verifique se o ID está correto."
        }
    )


@app.post("/jogos", status_code=status.HTTP_201_CREATED, response_model=JogoResponse, tags=["Jogos"],
          dependencies=[Depends(verificar_token)])
def criar_jogo(jogo: JogoBase):
    global proximo_id
    for j in banco_jogos:
        if j["nome"].lower() == jogo.nome.lower():
            raise HTTPException(
                status_code=409,
                detail={
                    "status": "erro",
                    "mensagem": f"Já existe um jogo com o nome '{jogo.nome}'. Use PUT /jogos/{j['id']} para atualizar."
                }
            )
    item = jogo.dict()
    item["id"] = proximo_id
    proximo_id += 1
    banco_jogos.append(item)
    return item


@app.put("/jogos/{id}", response_model=JogoResponse, tags=["Jogos"],
         dependencies=[Depends(verificar_token)])
def atualizar_jogo(id: int, jogo_atualizado: JogoBase):
    if id <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "erro",
                "mensagem": f"ID inválido: '{id}'. O ID deve ser um número inteiro positivo."
            }
        )
    for index, jogo in enumerate(banco_jogos):
        if jogo["id"] == id:
            for j in banco_jogos:
                if j["nome"].lower() == jogo_atualizado.nome.lower() and j["id"] != id:
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "status": "erro",
                            "mensagem": f"Já existe outro jogo com o nome '{jogo_atualizado.nome}'."
                        }
                    )
            item = jogo_atualizado.dict()
            item["id"] = id
            banco_jogos[index] = item
            return item
    raise HTTPException(
        status_code=404,
        detail={
            "status": "erro",
            "mensagem": f"Jogo com ID {id} não encontrado. Não é possível atualizar um jogo inexistente."
        }
    )


@app.delete("/jogos/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Jogos"],
            dependencies=[Depends(verificar_token)])
def deletar_jogo(id: int):
    if id <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "erro",
                "mensagem": f"ID inválido: '{id}'. O ID deve ser um número inteiro positivo."
            }
        )
    for index, jogo in enumerate(banco_jogos):
        if jogo["id"] == id:
            banco_jogos.pop(index)
            return None
    raise HTTPException(
        status_code=404,
        detail={
            "status": "erro",
            "mensagem": f"Jogo com ID {id} não encontrado. Não é possível deletar um jogo inexistente."
        }
    )