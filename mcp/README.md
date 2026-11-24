# MCP Server – Protocolos Corporativos

Pasta do **MCP customizado** que se conecta à API de Protocolos Corporativos.

## O que este MCP faz

Expõe tools que o Grok / Claude / Cursor podem chamar para consultar:

| Tool            | O que faz                                      |
|-----------------|------------------------------------------------|
| `list_users`    | Lista usuários (filtro ativo / departamento / estado) |
| `get_user`      | Detalhe de um usuário                          |
| `list_protocols`| Lista protocolos (compliance / risk / innovation) |
| `get_protocol`  | Protocolo + documentos                         |
| `list_documents`| Documentos/artefatos                           |
| `list_audits`   | Logs de login/logout                           |
| `get_costs`     | Tabela de custos por tipo de protocolo         |
| `list_emails`   | E-mails dos usuários                           |
| `list_payments` | Pagamentos individuais (filtros: usuário, estado, mês, categoria, status…) |
| `get_payments_summary` | Totais agrupados por usuário, estado, categoria, mês, protocolo ou departamento |
| `get_summary`   | Resumo geral (ótimo para artefatos)            |

## Pré-requisito

A API precisa estar rodando:

```bash
# na raiz do repositório
docker build -t protocolos-api .
docker run -p 8000:8000 protocolos-api
```

## Como rodar o MCP (local)

```bash
cd mcp
python -m venv .venv               # no Ubuntu sem python3-venv: uv venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # ou: uv pip install -r requirements.txt

# sobe o servidor em modo stdio
python server.py
```

Ou com o CLI do SDK:

```bash
mcp run server.py
# ou para testar no Inspector:
mcp dev server.py
```

## Conectar no host (Claude Desktop / Cursor / etc.)

Exemplo de configuração (Claude Desktop – `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "protocolos-corporativos": {
      "command": "/CAMINHO/ABSOLUTO/PARA/protocolos-corporativos-api/mcp/.venv/bin/python",
      "args": ["/CAMINHO/ABSOLUTO/PARA/protocolos-corporativos-api/mcp/server.py"],
      "env": {
        "PROTOCOLOS_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

Substitua `/CAMINHO/ABSOLUTO/...` pelo caminho real da pasta no seu computador.
Use o Python **do `.venv`** (no Windows: `...\mcp\.venv\Scripts\python.exe`); o Python do sistema não tem o pacote `mcp` e o servidor não sobe.

### Claude Code

```bash
claude mcp add protocolos-corporativos \
  -e PROTOCOLOS_API_URL=http://localhost:8000 \
  -- /CAMINHO/ABSOLUTO/PARA/protocolos-corporativos-api/mcp/.venv/bin/python \
     /CAMINHO/ABSOLUTO/PARA/protocolos-corporativos-api/mcp/server.py
```

Depois abra `claude` na pasta do projeto e confira com `/mcp`.

Depois de salvar a config e reiniciar o host, você poderá pedir:

> “Liste os protocolos de compliance e mostre o resumo de custos”
> “Quem gastou mais este mês? E quanto está previsto para o próximo?”
> “Qual estado tem mais gastos com viagem em 2026?”

O modelo vai usar as tools deste MCP automaticamente.

## Variável de ambiente

| Variável              | Default                 | Descrição                    |
|-----------------------|-------------------------|------------------------------|
| `PROTOCOLOS_API_URL`  | `http://localhost:8000` | Base URL da API de protocolos |

## Estrutura desta pasta

```
mcp/
├── server.py          # MCP server (tools)
├── requirements.txt   # mcp + httpx
└── README.md
```
