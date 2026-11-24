FROM python:3.12-slim

WORKDIR /app

# Dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código e dados
COPY app/ ./app/
COPY data/ ./data/

EXPOSE 8000

# Roda a API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
