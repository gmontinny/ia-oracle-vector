FROM python:3.10-slim

WORKDIR /app

# Copia o arquivo de dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos da aplicação
COPY . .
