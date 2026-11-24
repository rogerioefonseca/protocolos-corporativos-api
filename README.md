# Protocolos Corporativos API

API **simples e sem autenticação** com dados estáticos em JSON.  
Criada para demonstrar **integrações** e **MCP customizado** em aulas de IA para público não técnico.

## O que tem dentro

| Recurso       | Descrição                                      | Endpoint principal      |
|---------------|------------------------------------------------|-------------------------|
| Usuários      | 30 colaboradores com cidade/estado (UF) + protocolo | `GET /users?state=SP` |
| Protocolos    | 3 tipos: **compliance**, **risk**, **innovation** | `GET /protocols`     |
| Documentos    | Artefatos anexados a cada protocolo            | `GET /documents`        |
| Auditorias    | Logs de login/logout                           | `GET /audits`           |
| Custos        | 3 categorias de custo por tipo de protocolo    | `GET /costs`            |
| E-mails       | Endereços (corporativos e pessoais)            | `GET /emails`           |
| Pagamentos    | ~1.000 pagamentos de jan/2025 a dez/2027 (pagos e previstos) | `GET /payments` |
| Pagamentos (totais) | Totais por usuário, estado, categoria, mês… | `GET /payments/summary?group_by=user&month=2026-11` |
| Resumo        | Visão agregada (ótimo para dashboards)         | `GET /summary`          |

### Tipos de Protocolo

1. **compliance** – Conformidade Regulatória (LGPD, SOX…)
2. **risk** – Gestão de Riscos (cibersegurança, continuidade)
3. **innovation** – Inovação e Projetos (inovação aberta, transformação digital)

Cada tipo tem **3 custos**:
- `setup` – implantação
- `monthly` – recorrente mensal
- `per_document` – por documento/artefato

## Rodar localmente com Docker

```bash
# Build
docker build -t protocolos-api .

# Run
docker run -p 8000:8000 protocolos-api
```

Acesse:
- API: http://localhost:8000
- Documentação interativa (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Datas "vivas" (passado, presente e futuro)

Os status são calculados **pela data de hoje** a cada requisição, então a demo não fica velha:

- Pagamentos: até hoje → `pago`; depois de hoje → `previsto`
- Protocolos: antes do início → `planejado`; depois do fim → `encerrado`; senão o status salvo (`ativo` / `em_revisao`)

Para simular outra data (ex.: mostrar "o futuro" na aula), use `DEMO_TODAY`:

```bash
docker run -p 8000:8000 -e DEMO_TODAY=2027-06-15 protocolos-api
```

### Regenerar os dados

Os dados extras são gerados por `scripts/generate_data.py` (seed fixa, sempre o mesmo resultado).
Os 6 usuários/protocolos originais são preservados.

```bash
python scripts/generate_data.py
docker build -t protocolos-api .   # rebuild para a imagem pegar os novos JSON
```

### Exemplos rápidos

```bash
curl http://localhost:8000/users
curl http://localhost:8000/protocols?type=compliance
curl http://localhost:8000/protocols/prot-comp-01
curl http://localhost:8000/audits?success=false
curl http://localhost:8000/costs
curl http://localhost:8000/summary
curl "http://localhost:8000/users?state=SP"
curl "http://localhost:8000/payments?user_id=usr-006&month=2026-11"
curl "http://localhost:8000/payments/summary?group_by=state&status=previsto"
```

## Rodar sem Docker (Python)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## MCP Customizado

A pasta **`mcp/`** contém o servidor MCP que se conecta a esta API.

```bash
cd mcp
pip install -r requirements.txt
python server.py
```

Veja o [README da pasta mcp](mcp/README.md) para instruções de conexão no Claude Desktop, Cursor, Grok, etc.

## Estrutura do projeto

```
.
├── app/
│   └── main.py          # FastAPI
├── data/
│   ├── users.json
│   ├── protocols.json
│   ├── documents.json
│   ├── audits.json
│   ├── costs.json
│   ├── emails.json
│   └── payments.json
├── scripts/
│   └── generate_data.py # gera/expande os dados
├── mcp/                 # ← MCP customizado
│   ├── server.py
│   ├── requirements.txt
│   └── README.md
├── Dockerfile
├── requirements.txt
└── README.md
```

## Uso na aula (MCP / Integrações)

Esta API é perfeita para mostrar:

1. **Consumo de API** simples (sem auth)
2. Criação de **artefatos** (páginas, relatórios, dashboards) que leem `/summary` ou endpoints específicos
3. Construção de um **MCP server customizado** (já pronto na pasta `mcp/`)
4. Integração com Google Drive / Gmail (ex.: salvar relatório gerado, enviar e-mail de resumo)

Depois de rodar a API localmente, você pode conectar o MCP e experimentar as tools.

---

Feito para a aula **IA para o dia a dia**.
