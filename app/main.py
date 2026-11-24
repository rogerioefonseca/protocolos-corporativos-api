"""
Protocolos Corporativos API
API simples com dados estáticos para demonstração de integrações e MCP.
Sem autenticação — ideal para aula de IA para público não técnico.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import date
import json
import os
from typing import Literal, Optional

app = FastAPI(
    title="Protocolos Corporativos API",
    description="API demo com dados estáticos de usuários, protocolos, documentos, auditorias, custos e pagamentos. Pensada para ensinar MCP e integrações.",
    version="1.1.0",
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


def today() -> date:
    """Data de referência da demo. Por padrão é hoje; DEMO_TODAY=AAAA-MM-DD simula outra data."""
    override = os.getenv("DEMO_TODAY")
    return date.fromisoformat(override) if override else date.today()


def protocol_status(p: dict, ref: date) -> str:
    """Status calculado pela data: planejado (ainda não começou), encerrado (já terminou) ou o status salvo."""
    if date.fromisoformat(p["start_date"]) > ref:
        return "planejado"
    if date.fromisoformat(p["end_date"]) < ref:
        return "encerrado"
    return p.get("status", "ativo")


def load_protocols() -> list:
    ref = today()
    protocols = load_json("protocols.json")
    for p in protocols:
        p["status"] = protocol_status(p, ref)
    return protocols


# ---------- Health & Info ----------

@app.get("/", tags=["Info"])
def root():
    return {
        "message": "Protocolos Corporativos API",
        "version": "1.1.0",
        "docs": "/docs",
        "endpoints": [
            "/users",
            "/protocols",
            "/documents",
            "/audits",
            "/costs",
            "/emails",
            "/payments",
            "/payments/summary",
            "/summary",
        ],
        "today": today().isoformat(),
    }


@app.get("/health", tags=["Info"])
def health():
    return {"status": "ok"}


# ---------- Users ----------

@app.get("/users", tags=["Users"])
def list_users(
    active: Optional[bool] = Query(None, description="Filtrar por usuários ativos/inativos"),
    department: Optional[str] = Query(None, description="Filtrar por departamento"),
    state: Optional[str] = Query(None, description="Filtrar por estado (UF), ex: SP, MG, BA"),
):
    users = load_json("users.json")
    if active is not None:
        users = [u for u in users if u.get("active") == active]
    if department:
        users = [u for u in users if u.get("department", "").lower() == department.lower()]
    if state:
        users = [u for u in users if u.get("state", "").lower() == state.lower()]
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
    status: Optional[str] = Query(None, description="Filtrar por status: ativo | em_revisao | planejado | encerrado"),
):
    protocols = load_protocols()
    if type:
        protocols = [p for p in protocols if p.get("type") == type]
    if status:
        protocols = [p for p in protocols if p.get("status") == status]
    return protocols


@app.get("/protocols/{protocol_id}", tags=["Protocols"])
def get_protocol(protocol_id: str):
    protocols = load_protocols()
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


# ---------- Payments ----------

PAYMENT_CATEGORIES = "setup | mensalidade | documento | viagem | treinamento | software | consultoria | equipamento | alimentacao"


def filtered_payments(
    user_id: Optional[str] = None,
    protocol_id: Optional[str] = None,
    category: Optional[str] = None,
    state: Optional[str] = None,
    department: Optional[str] = None,
    month: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
) -> list:
    ref = today().isoformat()
    users = {u["id"]: u for u in load_json("users.json")}
    result = []
    for p in load_json("payments.json"):
        u = users.get(p["user_id"], {})
        p["status"] = "pago" if p["date"] <= ref else "previsto"
        p["user_name"] = u.get("name")
        p["state"] = u.get("state")
        p["department"] = u.get("department")
        if user_id and p["user_id"] != user_id:
            continue
        if protocol_id and p["protocol_id"] != protocol_id:
            continue
        if category and p["category"] != category:
            continue
        if state and (p["state"] or "").lower() != state.lower():
            continue
        if department and (p["department"] or "").lower() != department.lower():
            continue
        if month and not p["date"].startswith(month):
            continue
        if start_date and p["date"] < start_date:
            continue
        if end_date and p["date"] > end_date:
            continue
        if status and p["status"] != status:
            continue
        result.append(p)
    return result


@app.get("/payments", tags=["Payments"])
def list_payments(
    user_id: Optional[str] = Query(None),
    protocol_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None, description=PAYMENT_CATEGORIES),
    state: Optional[str] = Query(None, description="UF do usuário, ex: SP"),
    department: Optional[str] = Query(None, description="Compliance | Riscos | Inovação"),
    month: Optional[str] = Query(None, description="Mês no formato AAAA-MM"),
    start_date: Optional[str] = Query(None, description="AAAA-MM-DD (inclusive)"),
    end_date: Optional[str] = Query(None, description="AAAA-MM-DD (inclusive)"),
    status: Optional[str] = Query(None, description="pago (até hoje) | previsto (futuro)"),
):
    """Pagamentos de jan/2025 a dez/2027. Status é calculado pela data de hoje: pago ou previsto."""
    return filtered_payments(user_id, protocol_id, category, state, department, month, start_date, end_date, status)


@app.get("/payments/summary", tags=["Payments"])
def payments_summary(
    group_by: Literal["user", "state", "category", "month", "protocol", "department"] = Query("user"),
    user_id: Optional[str] = Query(None),
    protocol_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None, description=PAYMENT_CATEGORIES),
    state: Optional[str] = Query(None, description="UF do usuário, ex: SP"),
    department: Optional[str] = Query(None),
    month: Optional[str] = Query(None, description="Mês no formato AAAA-MM"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="pago | previsto"),
):
    """Totais de pagamentos agrupados (por usuário, estado, categoria, mês, protocolo ou departamento), do maior para o menor."""
    payments = filtered_payments(user_id, protocol_id, category, state, department, month, start_date, end_date, status)
    groups: dict = {}
    for p in payments:
        if group_by == "user":
            key, label = p["user_id"], f'{p["user_name"]} ({p["state"]})'
        elif group_by == "month":
            key = label = p["date"][:7]
        else:
            key = label = p[{"state": "state", "category": "category", "protocol": "protocol_id",
                             "department": "department"}[group_by]]
        g = groups.setdefault(key, {"key": key, "label": label, "total": 0.0, "paid": 0.0, "forecast": 0.0, "count": 0})
        g["total"] += p["amount"]
        g["paid" if p["status"] == "pago" else "forecast"] += p["amount"]
        g["count"] += 1
    rows = list(groups.values())
    for g in rows:
        for k in ("total", "paid", "forecast"):
            g[k] = round(g[k], 2)
    rows.sort(key=(lambda g: g["key"]) if group_by == "month" else (lambda g: -g["total"]))
    return {
        "today": today().isoformat(),
        "group_by": group_by,
        "currency": "BRL",
        "grand_total": round(sum(p["amount"] for p in payments), 2),
        "count": len(payments),
        "groups": rows,
    }


# ---------- Summary (útil para artefatos / dashboards) ----------

@app.get("/summary", tags=["Summary"])
def get_summary():
    users = load_json("users.json")
    protocols = load_protocols()
    payments = filtered_payments()
    month = today().isoformat()[:7]
    documents = load_json("documents.json")
    audits = load_json("audits.json")
    costs = load_json("costs.json")

    active_users = sum(1 for u in users if u.get("active"))
    total_protocol_value = sum(p.get("value", 0) for p in protocols)
    login_success = sum(1 for a in audits if a.get("action") == "login" and a.get("success"))
    login_failed = sum(1 for a in audits if a.get("action") == "login" and not a.get("success"))

    by_status: dict = {}
    for p in protocols:
        by_status[p["status"]] = by_status.get(p["status"], 0) + 1

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
            "by_state": {s: sum(1 for u in users if u.get("state") == s) for s in sorted({u.get("state") for u in users})},
        },
        "protocols": {
            "total": len(protocols),
            "total_value_brl": total_protocol_value,
            "by_type": by_type,
            "by_status": by_status,
        },
        "payments": {
            "today": today().isoformat(),
            "total_paid_brl": round(sum(p["amount"] for p in payments if p["status"] == "pago"), 2),
            "total_forecast_brl": round(sum(p["amount"] for p in payments if p["status"] == "previsto"), 2),
            "current_month": month,
            "current_month_brl": round(sum(p["amount"] for p in payments if p["date"].startswith(month)), 2),
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
