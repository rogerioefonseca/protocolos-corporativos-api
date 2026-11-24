# Protocolos Corporativos API

API **simples e sem autenticação** com dados estáticos em JSON.  
Criada para demonstrar **integrações** e **MCP customizado** em aulas de IA para público não técnico.

## O que tem dentro

| Recurso       | Descrição                                      | Endpoint principal      |
|---------------|------------------------------------------------|-------------------------|
| Usuários      | Lista de colaboradores + protocolo associado   | `GET /users`            |
| Protocolos    | 3 tipos: **compliance**, **risk**, **innovation** | `GET /protocols`     |
| Documentos    | Artefatos anexados a cada protocolo            | `GET /documents`        |
| Auditorias    | Logs de login/logout                           | `GET /audits`           |
| Custos        | 3 categorias de custo por tipo de protocolo    | `GET /costs`            |
| E-mails       | Endereços (corporativos e pessoais)            | `GET /emails`           |
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

### Exemplos rápidos

```bash
curl http://localhost:8000/users
curl http://localhost:8000/protocols?type=compliance
curl http://localhost:8000/protocols/prot-comp-01
curl http://localhost:8000/audits?success=false
curl http://localhost:8000/costs
curl http://localhost:8000/summary
```

## Rodar sem Docker (Python)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

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
│   └── emails.json
├── Dockerfile
├── requirements.txt
└── README.md
```

## Uso na aula (MCP / Integrações)

Esta API é perfeita para mostrar:

1. **Consumo de API** simples (sem auth)
2. Criação de **artefatos** (páginas, relatórios, dashboards) que leem `/summary` ou endpoints específicos
3. Construção de um **MCP server customizado** que expõe ferramentas como:
   - `list_protocols`
   - `get_user_audits`
   - `calculate_protocol_cost`
   - etc.
4. Integração com Google Drive / Gmail (ex.: salvar relatório gerado, enviar e-mail de resumo)

Depois de rodar a API localmente, você pode conectar um MCP CLI / cliente e experimentar as tools.

---

Feito para a aula **IA para o dia a dia**.
