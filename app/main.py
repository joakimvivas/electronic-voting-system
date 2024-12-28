# app/main.py
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.templating import Jinja2Templates
import uvicorn
import uuid
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Adjust the imports according to your file structure
from app.utils.encrypt import generate_key
from app.utils.file_ops import save_voting_file, load_voting_file
from app.utils.token_index import load_tokens_index, save_tokens_index

###############################
# MODELS
###############################

class VotacionCreate(BaseModel):
    titulo: str
    opciones: List[str]
    entidad: Optional[str] = None
    logotipo: Optional[str] = None

###############################
# FASTAPI INIT & JINJA2
###############################

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

###############################
# ENDPOINTS
###############################

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom handler for HTTPException to show an HTML error page.
    """
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "detail": exc.detail
        },
        status_code=exc.status_code
    )

@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Custom handler for Starlette HTTP exceptions (like 405)."""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "detail": exc.detail or "Method Not Allowed (or other Starlette HTTP error)"
        },
        status_code=exc.status_code
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """
    Specific handler for 404 errors, in case we want a custom page for 'page not found'.
    """
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 404,
            "detail": "La página que buscas no existe."
        },
        status_code=404
    )

@app.get("/", response_class=HTMLResponse)
def show_create_form(request: Request):
    """
    Root path: shows a small form to create a new voting with extra fields
    like entidad and logotipo.
    """
    return templates.TemplateResponse("create_form.html", {"request": request})


@app.post("/crear_votacion_form", response_class=HTMLResponse)
def crear_votacion_form(
    request: Request,
    titulo: str = Form(...),
    opciones: str = Form(...),
    entidad: str = Form(None),
    logotipo: str = Form(None)
):
    """
    Creates a new voting based on a form submission (www-form-urlencoded)
    and shows the result using a template.
    """
    # Convert comma-separated options into a list
    lista_opciones = [opt.strip() for opt in opciones.split(",") if opt.strip()]

    # Build the Pydantic object
    datos = VotacionCreate(
        titulo=titulo,
        opciones=lista_opciones,
        entidad=entidad,
        logotipo=logotipo
    )

    # Generate ID and key
    voting_id = str(uuid.uuid4())
    key = generate_key()

    # Prepare the voting data structure
    voting_data = {
        "metadata": {
            "voting_id": voting_id,
            "titulo": datos.titulo,
            "entidad": datos.entidad,
            "logotipo": datos.logotipo
        },
        "opciones": {op: 0 for op in datos.opciones},
        "votantes": {},
        "logs": [
            {
                "action": "CREATE_VOTACION",
                "voting_id": voting_id,
                "timestamp": datetime.now().isoformat()  # <- guardamos fecha/hora
            }
        ]
    }

    # Save the encrypted file
    save_voting_file(voting_id, voting_data, key)

    # Render a template showing the info
    return templates.TemplateResponse(
        "votacion_creada.html",
        {
            "request": request,
            "voting_id": voting_id,
            "admin_key": key.decode("utf-8"),
            "titulo": datos.titulo,
            "opciones": lista_opciones,
            "entidad": datos.entidad,
            "logotipo": datos.logotipo
        }
    )

@app.get("/admin_panel", response_class=HTMLResponse)
def admin_panel(request: Request, voting_id: str, key: str):
    """
    Decrypts the file and shows the admin panel (admin_panel.html).
    """
    try:
        voting_data = load_voting_file(voting_id, key.encode("utf-8"))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Voting not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid key or error decrypting data")

    return templates.TemplateResponse(
        "admin_panel.html",
        {
            "request": request,
            "voting_data": voting_data,
            "voting_id": voting_id,
            "key": key
        }
    )

@app.post("/anadir_votante")
def anadir_votante(
    voting_id: str = Form(...),
    key: str = Form(...),
    email: str = Form(...)
):
    """
    Adds a voter to the voting process and updates tokens_index.json.
    Redirects back to the admin panel.
    """
    # Load the current voting
    try:
        voting_data = load_voting_file(voting_id, key.encode("utf-8"))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Voting not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid key")

    # Generate a token for the voter
    token_votacion = str(uuid.uuid4())

    # Add the voter
    voting_data["votantes"][email] = {
        "ya_voto": False,
        "token_votacion": token_votacion
    }
    voting_data["logs"].append({
        "action": "ADD_VOTANTE",
        "email": email,
        "timestamp": datetime.now().isoformat()
    })

    # Save the updated voting
    save_voting_file(voting_id, voting_data, key.encode("utf-8"))

    # Update the token index
    index_data = load_tokens_index()
    index_data[token_votacion] = {
        "voting_id": voting_id,
        "key": key
    }
    save_tokens_index(index_data)

    # Redirect back to admin panel
    redirect_url = f"/admin_panel?voting_id={voting_id}&key={key}"
    return RedirectResponse(url=redirect_url, status_code=303)

@app.get("/admin_audit", response_class=HTMLResponse)
def admin_audit(request: Request, voting_id: str, key: str):
    """
    Shows the audit logs in a separate page.
    """
    try:
        voting_data = load_voting_file(voting_id, key.encode("utf-8"))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Voting not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid key")

    logs = voting_data.get("logs", [])

    return templates.TemplateResponse(
        "audit_logs.html",
        {
            "request": request,
            "logs": logs,
            "voting_id": voting_id,
            "key": key
        }
    )

@app.get("/votar", response_class=HTMLResponse)
def votar(request: Request, token: str):
    """
    Shows the voting form (votar.html) using Jinja2.
    """
    index_data = load_tokens_index()
    token_info = index_data.get(token)
    if not token_info:
        raise HTTPException(status_code=404, detail="Voting token is invalid")

    voting_id = token_info["voting_id"]
    key_str = token_info["key"]
    key_bytes = key_str.encode("utf-8")

    try:
        voting_data = load_voting_file(voting_id, key_bytes)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Voting not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid key")

    opciones = list(voting_data["opciones"].keys())
    metadata = voting_data.get("metadata", {})

    return templates.TemplateResponse(
        "votar.html",
        {
            "request": request,
            "token": token,
            "opciones": opciones,
            "metadata": metadata
        }
    )

@app.post("/emitir_voto", response_class=HTMLResponse)
def emitir_voto(
    request: Request,
    token: str = Form(...),
    opcion: str = Form(...)
):
    """
    Processes the vote and shows the result (resultado_voto.html).
    """
    index_data = load_tokens_index()
    token_info = index_data.get(token)
    if not token_info:
        raise HTTPException(status_code=404, detail="Invalid token")

    voting_id = token_info["voting_id"]
    key_str = token_info["key"]
    key_bytes = key_str.encode("utf-8")

    try:
        voting_data = load_voting_file(voting_id, key_bytes)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Voting not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid key")

    # Find the voter that has this token
    votante_email = None
    for email, vinfo in voting_data["votantes"].items():
        if vinfo["token_votacion"] == token:
            votante_email = email
            break

    if not votante_email:
        raise HTTPException(status_code=404, detail="Invalid voting token")

    # Check if the voter has already voted
    if voting_data["votantes"][votante_email]["ya_voto"]:
        return templates.TemplateResponse(
            "resultado_voto.html",
            {
                "request": request,
                "exito": False,
                "opcion": opcion
            }
        )

    if opcion not in voting_data["opciones"]:
        return templates.TemplateResponse(
            "resultado_voto.html",
            {
                "request": request,
                "exito": False,
                "opcion": opcion
            }
        )

    # Register the vote
    voting_data["opciones"][opcion] += 1
    voting_data["votantes"][votante_email]["ya_voto"] = True

    # Add a log
    voting_data["logs"].append({
        "action": "EMITIR_VOTO",
        "email": votante_email,
        "opcion": opcion,
        "timestamp": datetime.now().isoformat()
    })

    # Save
    save_voting_file(voting_id, voting_data, key_bytes)

    return templates.TemplateResponse(
        "resultado_voto.html",
        {
            "request": request,
            "exito": True,
            "opcion": opcion
        }
    )

@app.post("/delete_votante")
def delete_votante(
    voting_id: str = Form(...),
    key: str = Form(...),
    email: str = Form(...)
):
    """
    Deletes a voter if they haven't voted yet (ya_voto=False), 
    then redirects back to the admin panel.
    """
    try:
        voting_data = load_voting_file(voting_id, key.encode("utf-8"))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Voting not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid key")

    if email not in voting_data["votantes"]:
        raise HTTPException(status_code=404, detail="Voter not found")

    votante_info = voting_data["votantes"][email]
    if votante_info["ya_voto"]:
        raise HTTPException(status_code=400, detail="Cannot delete a voter who has already voted")

    token_votacion = votante_info["token_votacion"]

    del voting_data["votantes"][email]
    voting_data["logs"].append({
        "action": "REMOVE_VOTANTE",
        "email": email,
        "timestamp": datetime.now().isoformat()
    })

    # Remove from tokens_index
    index_data = load_tokens_index()
    if token_votacion in index_data:
        del index_data[token_votacion]
    save_tokens_index(index_data)

    save_voting_file(voting_id, voting_data, key.encode("utf-8"))

    redirect_url = f"/admin_panel?voting_id={voting_id}&key={key}"
    return RedirectResponse(url=redirect_url, status_code=303)

# Startup
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
