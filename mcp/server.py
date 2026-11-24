"""
MCP Server – Protocolos Corporativos

Conecta um host MCP (Claude Desktop, Cursor, Grok, etc.) à API
de Protocolos Corporativos (http://localhost:8000 por padrão).

Uso típico na aula:
  1. Suba a API com Docker
  2. Rode este MCP (stdio)
  3. Conecte o host apontando para este arquivo
"""

from __future__ import annotations

import os
from typing import Optional

import httpx
from mcp.server import MCPServer

# URL base da API. Pode ser sobrescrita por variável de ambiente.
API_BASE = os.getenv("PROTOCOLOS_API_URL", "http://localhost:8000").rstrip("/")

mcp = MCPServer(
    "protocolos-corporativos",
    instructions=(
        "Você tem acesso à API de Protocolos Corporativos da empresa. "
        "Use as tools para consultar usuários, protocolos (compliance / risk / innovation), "
        "documentos, auditorias de login, custos, pagamentos e o resumo geral. "
        "Cada usuário tem cidade e estado (UF). Os pagamentos vão de jan/2025 a dez/2027: "
        "os até hoje têm status 'pago' e os futuros 'previsto'. "
        "Para totais e rankings prefira get_payments_summary (já agregado) em vez de somar list_payments. "
        "As respostas trazem 'today' com a data de referência; use-a para interpretar 'este mês', 'próximo mês' etc. "
        "Os dados são fictícios e servem para demonstração de integração via MCP."
    ),
)


def _get(path: str, params: dict | None = None) -> dict | list:
    """Chamada GET simples à API. Levanta exceção clara se a API estiver fora."""
    url = f"{API_BASE}{path}"
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(url, params=params or {})
            r.raise_for_status()
            return r.json()
    except httpx.ConnectError:
        raise RuntimeError(
            f"Não foi possível conectar em {API_BASE}. "
            "Verifique se a API está rodando (docker run -p 8000:8000 protocolos-api)."
        )
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"API retornou {e.response.status_code}: {e.response.text}") from e


# ---------- Tools ----------

@mcp.tool()
def list_users(
    active: Optional[bool] = None,
    department: Optional[str] = None,
    state: Optional[str] = None,
) -> list:
    """Lista os usuários da empresa (com cidade e estado). Filtros: ativo/inativo, departamento (Compliance, Riscos, Inovação) e estado (UF, ex: SP, MG, BA)."""
    params = {}
    if active is not None:
        params["active"] = active
    if department:
        params["department"] = department
    if state:
        params["state"] = state
    return _get("/users", params)


@mcp.tool()
def get_user(user_id: str) -> dict:
    """Retorna os detalhes de um usuário pelo ID (ex: usr-001)."""
    return _get(f"/users/{user_id}")


@mcp.tool()
def list_protocols(
    type: Optional[str] = None,
    status: Optional[str] = None,
) -> list:
    """Lista os protocolos corporativos. Tipos: compliance, risk, innovation. Status (calculado pela data de hoje): ativo, em_revisao, planejado, encerrado."""
    params = {}
    if type:
        params["type"] = type
    if status:
        params["status"] = status
    return _get("/protocols", params)


@mcp.tool()
def get_protocol(protocol_id: str) -> dict:
    """Retorna um protocolo completo (incluindo seus documentos) pelo ID (ex: prot-comp-01)."""
    return _get(f"/protocols/{protocol_id}")


@mcp.tool()
def list_documents(
    protocol_id: Optional[str] = None,
    type: Optional[str] = None,
) -> list:
    """Lista documentos/artefatos. Pode filtrar por protocol_id ou tipo (politica, relatorio, plano, etc.)."""
    params = {}
    if protocol_id:
        params["protocol_id"] = protocol_id
    if type:
        params["type"] = type
    return _get("/documents", params)


@mcp.tool()
def list_audits(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    success: Optional[bool] = None,
) -> list:
    """Lista auditorias de login/logout. Útil para demonstrar segurança e rastreabilidade."""
    params = {}
    if user_id:
        params["user_id"] = user_id
    if action:
        params["action"] = action
    if success is not None:
        params["success"] = success
    return _get("/audits", params)


@mcp.tool()
def get_costs(protocol_type: Optional[str] = None) -> list:
    """Retorna a tabela de custos por tipo de protocolo (setup, monthly, per_document). Tipos: compliance, risk, innovation."""
    params = {}
    if protocol_type:
        params["protocol_type"] = protocol_type
    return _get("/costs", params)


@mcp.tool()
def list_emails(
    user_id: Optional[str] = None,
    type: Optional[str] = None,
) -> list:
    """Lista e-mails dos usuários (corporativo e pessoal)."""
    params = {}
    if user_id:
        params["user_id"] = user_id
    if type:
        params["type"] = type
    return _get("/emails", params)


def _payment_params(**kwargs) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


@mcp.tool()
def list_payments(
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
    """Lista pagamentos individuais (data, usuário, estado, protocolo, categoria, valor, status pago/previsto).
    Categorias: setup, mensalidade, documento, viagem, treinamento, software, consultoria, equipamento, alimentacao.
    month no formato AAAA-MM; start_date/end_date AAAA-MM-DD; status: pago | previsto.
    Use filtros: sem filtro retorna mais de mil linhas."""
    return _get("/payments", _payment_params(
        user_id=user_id, protocol_id=protocol_id, category=category, state=state, department=department,
        month=month, start_date=start_date, end_date=end_date, status=status))


@mcp.tool()
def get_payments_summary(
    group_by: str = "user",
    user_id: Optional[str] = None,
    protocol_id: Optional[str] = None,
    category: Optional[str] = None,
    state: Optional[str] = None,
    department: Optional[str] = None,
    month: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
) -> dict:
    """Totais de pagamentos agrupados e ordenados do maior para o menor (por mês: em ordem cronológica).
    group_by: user | state | category | month | protocol | department.
    Mesmos filtros de list_payments. Ex: quem gastou mais este mês -> group_by='user', month='AAAA-MM'.
    Cada grupo traz total, paid (já pago), forecast (previsto) e count."""
    return _get("/payments/summary", _payment_params(
        group_by=group_by, user_id=user_id, protocol_id=protocol_id, category=category, state=state,
        department=department, month=month, start_date=start_date, end_date=end_date, status=status))


@mcp.tool()
def get_summary() -> dict:
    """Retorna um resumo geral: data de hoje, usuários (por estado), protocolos (por tipo e status), pagamentos (pago, previsto, mês atual), logins e custos. Ideal para dashboards e artefatos."""
    return _get("/summary")


if __name__ == "__main__":
    # Transporte padrão: stdio (o que a maioria dos hosts espera)
    mcp.run()
