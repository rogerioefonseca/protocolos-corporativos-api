"""
Gera/expande os dados de demonstração em data/*.json.

- Mantém os registros originais (usr-001..006, 6 protocolos, doc-001..014,
  email-001..009, aud-001..010) e acrescenta city/state aos usuários.
- Gera usuários, protocolos, documentos, e-mails, auditorias e pagamentos extras.
- Determinístico (seed fixa): rodar de novo produz exatamente os mesmos arquivos.

Uso (na raiz do repositório):
    python scripts/generate_data.py
"""

from __future__ import annotations

import json
import random
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
rng = random.Random(42)

# Janela dos pagamentos: passado + futuro, para sempre haver "este mês" e "próximo mês".
PAY_START = date(2025, 1, 1)
PAY_END = date(2027, 12, 31)
# Auditorias (logins) vão até esta data; não faz sentido haver login no futuro.
AUDIT_END = date(2026, 11, 24)

STATES = {
    "AC": ("Acre", "Rio Branco"), "AL": ("Alagoas", "Maceió"), "AP": ("Amapá", "Macapá"),
    "AM": ("Amazonas", "Manaus"), "BA": ("Bahia", "Salvador"), "CE": ("Ceará", "Fortaleza"),
    "DF": ("Distrito Federal", "Brasília"), "ES": ("Espírito Santo", "Vitória"),
    "GO": ("Goiás", "Goiânia"), "MA": ("Maranhão", "São Luís"), "MT": ("Mato Grosso", "Cuiabá"),
    "MS": ("Mato Grosso do Sul", "Campo Grande"), "MG": ("Minas Gerais", "Belo Horizonte"),
    "PA": ("Pará", "Belém"), "PB": ("Paraíba", "João Pessoa"), "PR": ("Paraná", "Curitiba"),
    "PE": ("Pernambuco", "Recife"), "PI": ("Piauí", "Teresina"), "RJ": ("Rio de Janeiro", "Rio de Janeiro"),
    "RN": ("Rio Grande do Norte", "Natal"), "RS": ("Rio Grande do Sul", "Porto Alegre"),
    "RO": ("Rondônia", "Porto Velho"), "RR": ("Roraima", "Boa Vista"), "SC": ("Santa Catarina", "Florianópolis"),
    "SP": ("São Paulo", "São Paulo"), "SE": ("Sergipe", "Aracaju"), "TO": ("Tocantins", "Palmas"),
}
# Algumas cidades do interior para variar
EXTRA_CITIES = {
    "SP": ["Campinas", "Ribeirão Preto", "Santos"], "MG": ["Uberlândia", "Juiz de Fora"],
    "PR": ["Londrina", "Maringá"], "SC": ["Joinville", "Blumenau"], "RS": ["Caxias do Sul"],
    "BA": ["Feira de Santana"], "PE": ["Caruaru"], "RJ": ["Niterói"],
}

ORIGINAL_LOCATIONS = {
    "usr-001": ("São Paulo", "SP"), "usr-002": ("Rio de Janeiro", "RJ"),
    "usr-003": ("Belo Horizonte", "MG"), "usr-004": ("Curitiba", "PR"),
    "usr-005": ("Porto Alegre", "RS"), "usr-006": ("São Paulo", "SP"),
}

# (nome, departamento, cargo, UF)
NEW_USERS = [
    ("Gabriela Rocha", "Compliance", "Coordenadora de Compliance", "BA"),
    ("Henrique Almeida", "Riscos", "Analista de Riscos", "SP"),
    ("Isabela Martins", "Inovação", "UX Researcher", "SC"),
    ("João Pedro Lima", "Compliance", "Auditor Interno", "DF"),
    ("Karina Souza", "Riscos", "Especialista em Continuidade", "PE"),
    ("Lucas Barbosa", "Inovação", "Engenheiro de Dados", "MG"),
    ("Mariana Carvalho", "Compliance", "Analista Pleno", "CE"),
    ("Nicolas Ribeiro", "Riscos", "Analista de Segurança", "RS"),
    ("Olívia Gomes", "Inovação", "Gerente de Inovação", "SP"),
    ("Paulo Henrique Dias", "Compliance", "Gerente de Compliance", "RJ"),
    ("Quésia Nascimento", "Riscos", "Analista Júnior", "AM"),
    ("Rafael Teixeira", "Inovação", "Desenvolvedor Sênior", "PR"),
    ("Sabrina Moreira", "Compliance", "DPO", "GO"),
    ("Thiago Cardoso", "Riscos", "Coordenador de Riscos", "ES"),
    ("Úrsula Pires", "Inovação", "Designer de Serviços", "PA"),
    ("Vinícius Araújo", "Compliance", "Analista Júnior", "MT"),
    ("Wesley Fernandes", "Riscos", "Gerente de Segurança da Informação", "SP"),
    ("Yasmin Castro", "Inovação", "Cientista de Dados", "RN"),
    ("Arthur Monteiro", "Compliance", "Especialista Regulatório", "MS"),
    ("Beatriz Lopes", "Riscos", "Analista Pleno", "PB"),
    ("Caio Batista", "Inovação", "Arquiteto de Soluções", "SC"),
    ("Débora Freitas", "Compliance", "Analista Sênior", "MA"),
    ("Eduardo Vieira", "Riscos", "Especialista em Fraude", "MG"),
    ("Fernanda Rezende", "Inovação", "Product Manager", "SE"),
]
INACTIVE_NEW = {"Quésia Nascimento", "Vinícius Araújo"}  # saíram da empresa
LEFT_AT = date(2025, 12, 15)

# (id, tipo, nome, descrição, início, fim, em_revisao)
NEW_PROTOCOLS = [
    ("prot-comp-03", "compliance", "Protocolo Anticorrupção (Lei 12.846)",
     "Programa de integridade, due diligence de terceiros e canal de denúncias.",
     "2025-06-01", "2027-05-31", False),
    ("prot-comp-04", "compliance", "Protocolo ESG & Relato de Sustentabilidade",
     "Coleta de indicadores ESG e preparação do relatório anual de sustentabilidade.",
     "2026-01-01", "2027-12-31", False),
    ("prot-comp-05", "compliance", "Protocolo PCI-DSS Pagamentos",
     "Adequação dos fluxos de cartão ao padrão PCI-DSS 4.0.",
     "2026-09-01", "2028-02-29", False),
    ("prot-comp-06", "compliance", "Protocolo LGPD & Privacidade 2026-2027",
     "Renovação do programa de privacidade, com foco em IA e dados sensíveis.",
     "2026-01-01", "2027-12-31", True),
    ("prot-risk-03", "risk", "Protocolo de Riscos de Terceiros",
     "Avaliação contínua de fornecedores críticos e riscos da cadeia de suprimentos.",
     "2025-09-01", "2027-08-31", False),
    ("prot-risk-04", "risk", "Protocolo de Prevenção a Fraudes",
     "Monitoramento transacional e modelos de detecção de fraude.",
     "2026-03-01", "2028-02-29", False),
    ("prot-risk-05", "risk", "Protocolo de Riscos Climáticos",
     "Mapeamento de riscos físicos e de transição climática nas operações.",
     "2027-02-01", "2028-12-31", False),
    ("prot-risk-06", "risk", "Protocolo de Resposta a Incidentes 2.0",
     "Atualização do plano de resposta a incidentes e exercícios de mesa trimestrais.",
     "2026-05-01", "2027-04-30", True),
    ("prot-inn-03", "innovation", "Protocolo IA Generativa na Operação",
     "Pilotos de IA generativa em atendimento, jurídico e backoffice.",
     "2025-10-01", "2027-09-30", False),
    ("prot-inn-04", "innovation", "Protocolo Hub de Startups Nordeste",
     "Programa de conexão com startups do Nordeste e provas de conceito.",
     "2026-02-01", "2027-07-31", False),
    ("prot-inn-05", "innovation", "Protocolo Dados como Produto",
     "Plataforma de dados com domínios, catálogo e governança federada.",
     "2026-07-01", "2028-06-30", False),
    ("prot-inn-06", "innovation", "Protocolo Experiência do Cliente Omnicanal",
     "Redesenho da jornada do cliente em canais digitais e físicos.",
     "2027-01-01", "2028-12-31", False),
]

DEPT_TYPE = {"Compliance": "compliance", "Riscos": "risk", "Inovação": "innovation"}

DOC_TEMPLATES = {
    "compliance": [("Política", "politica", "pdf"), ("Matriz de Controles", "matriz", "xlsx"),
                   ("Checklist de Conformidade", "checklist", "pdf"), ("Relatório de Auditoria", "relatorio", "pdf")],
    "risk": [("Matriz de Riscos", "matriz", "xlsx"), ("Plano de Mitigação", "plano", "docx"),
             ("Relatório de Incidentes", "relatorio", "pdf"), ("Avaliação de Fornecedor", "avaliacao", "pdf")],
    "innovation": [("Roadmap", "roadmap", "pptx"), ("Documento de Arquitetura", "arquitetura", "pdf"),
                   ("Guia de Boas Práticas", "guia", "pdf"), ("Contrato de Parceria", "contrato", "pdf")],
}

# Despesas individuais (categoria, descrição, faixa de valor)
EXTRA_EXPENSES = [
    ("viagem", "Passagem aérea - reunião com fornecedor", (900, 3200)),
    ("viagem", "Hospedagem - visita a filial", (450, 1800)),
    ("treinamento", "Curso de certificação", (1200, 6500)),
    ("treinamento", "Inscrição em congresso do setor", (800, 4200)),
    ("software", "Licença de ferramenta (anual)", (600, 5400)),
    ("consultoria", "Horas de consultoria especializada", (3500, 18000)),
    ("equipamento", "Notebook / periféricos", (1500, 9800)),
    ("alimentacao", "Almoço de trabalho com cliente", (120, 680)),
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X)",
]


def slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    parts = s.split()
    return f"{parts[0]}.{parts[-1]}"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def save(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def months(start: date, end: date):
    d = date(start.year, start.month, 1)
    while d <= end:
        yield d
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def d(s: str) -> date:
    return date.fromisoformat(s)


def money(x: float) -> float:
    return round(x, 2)


def main():
    costs = {c["protocol_type"]: {k: v["value"] for k, v in c["costs"].items()} for c in load("costs.json")}

    # ---------- Usuários ----------
    original_ids = set(ORIGINAL_LOCATIONS)
    users = [u for u in load("users.json") if u["id"] in original_ids]
    for u in users:
        city, uf = ORIGINAL_LOCATIONS[u["id"]]
        u["city"], u["state"], u["state_name"] = city, uf, STATES[uf][0]

    for i, (name, dept, role, uf) in enumerate(NEW_USERS, start=7):
        city = STATES[uf][1]
        if uf in EXTRA_CITIES and rng.random() < 0.4:
            city = rng.choice(EXTRA_CITIES[uf])
        created = date(2024, 1, 1) + timedelta(days=rng.randint(0, 700))
        users.append({
            "id": f"usr-{i:03d}",
            "name": name,
            "email": f"{slug(name)}@empresa.com.br",
            "department": dept,
            "role": role,
            "protocol_id": None,  # preenchido abaixo
            "active": name not in INACTIVE_NEW,
            "created_at": f"{created.isoformat()}T{rng.randint(8, 17):02d}:{rng.randint(0, 59):02d}:00Z",
            "city": city,
            "state": uf,
            "state_name": STATES[uf][0],
        })

    # ---------- Protocolos ----------
    protocols = [p for p in load("protocols.json") if p["id"].split("-")[-1] in ("01", "02")]
    # Donos dos novos protocolos: usuários ativos do departamento correspondente, sem protocolo ainda
    free = {t: [u for u in users if u["protocol_id"] is None and u["active"] and DEPT_TYPE[u["department"]] == t]
            for t in ("compliance", "risk", "innovation")}
    for pid, ptype, name, desc, start, end, review in NEW_PROTOCOLS:
        owner = free[ptype].pop(0)
        owner["protocol_id"] = pid
        n_months = len(list(months(d(start), d(end))))
        c = costs[ptype]
        value = round((c["setup"] + c["monthly"] * n_months) * rng.uniform(1.05, 1.25), -3)
        protocols.append({
            "id": pid, "type": ptype, "name": name, "description": desc,
            "value": value, "currency": "BRL",
            "status": "em_revisao" if review else "ativo",
            "owner_user_id": owner["id"],
            "start_date": start, "end_date": end,
            "document_ids": [],
        })
    # Demais usuários sem protocolo entram como membros de um protocolo do seu departamento
    for u in users:
        if u["protocol_id"] is None:
            options = [p for p in protocols if p["type"] == DEPT_TYPE[u["department"]]]
            u["protocol_id"] = rng.choice(options)["id"]

    by_protocol = {p["id"]: p for p in protocols}
    members = {p["id"]: [u for u in users if u["protocol_id"] == p["id"]] for p in protocols}

    # ---------- Documentos ----------
    documents = [x for x in load("documents.json") if int(x["id"].split("-")[1]) <= 14]
    for doc in documents:
        by_protocol[doc["protocol_id"]]  # sanity
    next_doc = 15
    for p in protocols[6:]:
        start, end = d(p["start_date"]), min(d(p["end_date"]), PAY_END)
        for _ in range(rng.randint(2, 5)):
            title, dtype, fmt = rng.choice(DOC_TEMPLATES[p["type"]])
            created = start + timedelta(days=rng.randint(5, max(6, (end - start).days)))
            updated = created + timedelta(days=rng.randint(0, 120))
            documents.append({
                "id": f"doc-{next_doc:03d}",
                "protocol_id": p["id"],
                "title": f"{title} - {p['name'].replace('Protocolo ', '')}",
                "type": dtype, "format": fmt,
                "version": f"{rng.randint(1, 3)}.{rng.randint(0, 9)}",
                "created_at": f"{created.isoformat()}T{rng.randint(8, 18):02d}:00:00Z",
                "updated_at": f"{updated.isoformat()}T{rng.randint(8, 18):02d}:00:00Z",
                "size_kb": rng.randint(150, 4000),
                "tags": [p["type"], dtype],
            })
            p["document_ids"].append(f"doc-{next_doc:03d}")
            next_doc += 1
    documents.sort(key=lambda x: x["id"])

    # ---------- E-mails ----------
    emails = [e for e in load("emails.json") if int(e["id"].split("-")[1]) <= 9]
    n = 10
    providers = ["gmail.com", "outlook.com", "hotmail.com", "proton.me", "yahoo.com.br"]
    for u in users[6:]:
        emails.append({"id": f"email-{n:03d}", "user_id": u["id"], "address": u["email"],
                       "type": "corporativo", "primary": True, "verified": True})
        n += 1
        if rng.random() < 0.5:
            emails.append({"id": f"email-{n:03d}", "user_id": u["id"],
                           "address": f"{slug(u['name']).replace('.', '_')}@{rng.choice(providers)}",
                           "type": "pessoal", "primary": False, "verified": rng.random() < 0.8})
            n += 1

    # ---------- Auditorias ----------
    audits = [a for a in load("audits.json") if int(a["id"].split("-")[1]) <= 10]
    events = []
    for u in users:
        last = LEFT_AT if not u["active"] else AUDIT_END
        for _ in range(rng.randint(3, 8)):
            day = last - timedelta(days=rng.randint(0, 120))
            ts = datetime(day.year, day.month, day.day, rng.randint(7, 22), rng.randint(0, 59), rng.randint(0, 59))
            ok = rng.random() > 0.12
            events.append((ts, u, "login", ok))
            if ok and rng.random() < 0.6:
                events.append((ts + timedelta(hours=rng.randint(1, 9)), u, "logout", True))
    events.sort(key=lambda e: e[0])
    n = 11
    for ts, u, action, ok in events:
        audits.append({
            "id": f"aud-{n:03d}", "user_id": u["id"], "action": action, "success": ok,
            "ip": f"{rng.choice([177, 179, 187, 189, 191, 200, 201])}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}",
            "user_agent": rng.choice(USER_AGENTS),
            "timestamp": ts.isoformat() + "Z",
            "location": f"{u['city']}, BR" if ok or rng.random() < 0.5 else "Unknown",
        })
        n += 1

    # ---------- Pagamentos ----------
    raw = []
    for p in protocols:
        c = costs[p["type"]]
        owner = p["owner_user_id"]
        start, end = d(p["start_date"]), d(p["end_date"])
        if PAY_START <= start <= PAY_END:
            raw.append((start + timedelta(days=rng.randint(0, 10)), owner, p["id"], "setup",
                        "Implantação do protocolo", money(c["setup"] * rng.uniform(0.95, 1.1))))
        for m in months(max(start, PAY_START), min(end, PAY_END)):
            raw.append((m + timedelta(days=rng.randint(4, 9)), owner, p["id"], "mensalidade",
                        f"Mensalidade {m.strftime('%m/%Y')}", money(c["monthly"] * rng.uniform(0.92, 1.12))))
        team = members[p["id"]] or [next(u for u in users if u["id"] == owner)]
        for doc_id in p["document_ids"]:
            doc = next(x for x in documents if x["id"] == doc_id)
            when = d(doc["created_at"][:10])
            if PAY_START <= when <= PAY_END:
                raw.append((when, rng.choice(team)["id"], p["id"], "documento",
                            f"Elaboração: {doc['title']}", money(c["per_document"] * rng.uniform(0.8, 1.6))))

    for u in users:
        last = LEFT_AT if not u["active"] else PAY_END
        for m in months(PAY_START, last):
            for _ in range(rng.choices([0, 1, 2], weights=[45, 40, 15])[0]):
                cat, desc, (lo, hi) = rng.choice(EXTRA_EXPENSES)
                day = m + timedelta(days=rng.randint(0, 27))
                if day > last:
                    continue
                raw.append((day, u["id"], u["protocol_id"], cat, desc, money(rng.uniform(lo, hi))))

    raw.sort(key=lambda r: (r[0], r[1]))
    methods = {"setup": "transferencia", "mensalidade": "boleto"}
    payments = []
    for i, (day, uid, pid, cat, desc, amount) in enumerate(raw, start=1):
        payments.append({
            "id": f"pay-{i:05d}", "date": day.isoformat(), "user_id": uid, "protocol_id": pid,
            "category": cat, "description": desc, "amount": amount, "currency": "BRL",
            "method": methods.get(cat, rng.choice(["cartao_corporativo", "reembolso", "transferencia"])),
        })

    save("users.json", users)
    save("protocols.json", protocols)
    save("documents.json", documents)
    save("emails.json", emails)
    save("audits.json", audits)
    save("payments.json", payments)
    print(f"users={len(users)} protocols={len(protocols)} documents={len(documents)} "
          f"emails={len(emails)} audits={len(audits)} payments={len(payments)}")


if __name__ == "__main__":
    main()
