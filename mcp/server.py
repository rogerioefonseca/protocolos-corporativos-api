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
        "documentos, auditorias de login, custos e o resumo geral. "
        "Os dados são estáticos e servem para demonstração de integração via MCP."
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
) -> list:
    """Lista os usuários da empresa. Pode filtrar por ativo/inativo e por departamento (Compliance, Riscos, Inovação)."""
    params = {}
    if active is not None:
        params["active"] = active
    if department:
        params["department"] = department
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
    """Lista os protocolos corporativos. Tipos: compliance, risk, innovation. Status: ativo, em_revisao."""
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


@mcp.tool()
def get_summary() -> dict:
    """Retorna um resumo geral: totais de usuários, protocolos, valor total, logins com sucesso/falha e custos. Ideal para dashboards e artefatos."""
    return _get("/summary")


if __name__ == "__main__":
    # Transporte padrão: stdio (o que a maioria dos hosts espera)
    mcp.run()
