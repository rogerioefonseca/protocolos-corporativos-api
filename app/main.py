"""
Protocolos Corporativos API
API simples com dados estáticos para demonstração de integrações e MCP.
Sem autenticação — ideal para aula de IA para público não técnico.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from typing import Optional

app = FastAPI(
    title="Protocolos Corporativos API",
    description="API demo com dados estáticos de usuários, protocolos, documentos, auditorias e custos. Pensada para ensinar MCP e integrações.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent.parent / "data"


def load_json(filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=500, detail=f"Arquivo de dados não encontrado: {filename}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------- Health & Info ----------

@app.get("/", tags=["Info"])
def root():
    return {
        "message": "Protocolos Corporativos API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": [
            "/users",
            "/protocols",
            "/documents",
            "/audits",
            "/costs",
            "/emails",
            "/summary",
        ],
    }


@app.get("/health", tags=["Info"])
def health():
    return {"status": "ok"}


# ---------- Users ----------

@app.get("/users", tags=["Users"])
def list_users(
    active: Optional[bool] = Query(None, description="Filtrar por usuários ativos/inativos"),
    department: Optional[str] = Query(None, description="Filtrar por departamento"),
):
    users = load_json("users.json")
    if active is not None:
        users = [u for u in users if u.get("active") == active]
    if department:
        users = [u for u in users if u.get("department", "").lower() == department.lower()]
    return users


@app.get("/users/{user_id}", tags=["Users"])
def get_user(user_id: str):
    users = load_json("users.json")
    for u in users:
        if u["id"] == user_id:
            return u
    raise HTTPException(status_code=404, detail="Usuário não encontrado")


# ---------- Protocols ----------

@app.get("/protocols", tags=["Protocols"])
def list_protocols(
    type: Optional[str] = Query(None, description="Filtrar por tipo: compliance | risk | innovation"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
):
    protocols = load_json("protocols.json")
    if type:
        protocols = [p for p in protocols if p.get("type") == type]
    if status:
        protocols = [p for p in protocols if p.get("status") == status]
    return protocols


@app.get("/protocols/{protocol_id}", tags=["Protocols"])
def get_protocol(protocol_id: str):
    protocols = load_json("protocols.json")
    for p in protocols:
        if p["id"] == protocol_id:
            docs = load_json("documents.json")
            p["documents"] = [d for d in docs if d["protocol_id"] == protocol_id]
            return p
    raise HTTPException(status_code=404, detail="Protocolo não encontrado")


@app.get("/protocols/{protocol_id}/documents", tags=["Protocols"])
def get_protocol_documents(protocol_id: str):
    protocols = load_json("protocols.json")
    if not any(p["id"] == protocol_id for p in protocols):
        raise HTTPException(status_code=404, detail="Protocolo não encontrado")
    docs = load_json("documents.json")
    return [d for d in docs if d["protocol_id"] == protocol_id]


# ---------- Documents ----------

@app.get("/documents", tags=["Documents"])
def list_documents(
    protocol_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None, description="Tipo do documento (politica, relatorio, etc.)"),
):
    docs = load_json("documents.json")
    if protocol_id:
        docs = [d for d in docs if d.get("protocol_id") == protocol_id]
    if type:
        docs = [d for d in docs if d.get("type") == type]
    return docs


@app.get("/documents/{document_id}", tags=["Documents"])
def get_document(document_id: str):
    docs = load_json("documents.json")
    for d in docs:
        if d["id"] == document_id:
            return d
    raise HTTPException(status_code=404, detail="Documento não encontrado")


# ---------- Audits ----------

@app.get("/audits", tags=["Audits"])
def list_audits(
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None, description="login | logout"),
    success: Optional[bool] = Query(None),
):
    audits = load_json("audits.json")
    if user_id:
        audits = [a for a in audits if a.get("user_id") == user_id]
    if action:
        audits = [a for a in audits if a.get("action") == action]
    if success is not None:
        audits = [a for a in audits if a.get("success") == success]
    return audits


# ---------- Costs ----------

@app.get("/costs", tags=["Costs"])
def list_costs(protocol_type: Optional[str] = Query(None, description="compliance | risk | innovation")):
    costs = load_json("costs.json")
    if protocol_type:
        costs = [c for c in costs if c.get("protocol_type") == protocol_type]
    return costs


# ---------- Emails ----------

@app.get("/emails", tags=["Emails"])
def list_emails(
    user_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None, description="corporativo | pessoal"),
    primary: Optional[bool] = Query(None),
):
    emails = load_json("emails.json")
    if user_id:
        emails = [e for e in emails if e.get("user_id") == user_id]
    if type:
        emails = [e for e in emails if e.get("type") == type]
    if primary is not None:
        emails = [e for e in emails if e.get("primary") == primary]
    return emails


# ---------- Summary (útil para artefatos / dashboards) ----------

@app.get("/summary", tags=["Summary"])
def get_summary():
    users = load_json("users.json")
    protocols = load_json("protocols.json")
    documents = load_json("documents.json")
    audits = load_json("audits.json")
    costs = load_json("costs.json")

    active_users = sum(1 for u in users if u.get("active"))
    total_protocol_value = sum(p.get("value", 0) for p in protocols)
    login_success = sum(1 for a in audits if a.get("action") == "login" and a.get("success"))
    login_failed = sum(1 for a in audits if a.get("action") == "login" and not a.get("success"))

    by_type = {}
    for p in protocols:
        t = p.get("type", "unknown")
        by_type.setdefault(t, {"count": 0, "total_value": 0})
        by_type[t]["count"] += 1
        by_type[t]["total_value"] += p.get("value", 0)

    return {
        "users": {
            "total": len(users),
            "active": active_users,
            "inactive": len(users) - active_users,
        },
        "protocols": {
            "total": len(protocols),
            "total_value_brl": total_protocol_value,
            "by_type": by_type,
        },
        "documents": {
            "total": len(documents),
        },
        "audits": {
            "total": len(audits),
            "login_success": login_success,
            "login_failed": login_failed,
        },
        "costs": costs,
    }
