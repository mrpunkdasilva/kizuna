# Usar uma imagem base oficial do Python mais leve
FROM python:3.11-slim

# Instalar wget e dependências básicas do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Criar um usuário não-root para a aplicação
RUN useradd --create-home appuser
WORKDIR /home/appuser/app
USER appuser

# Adicionar o diretório bin local do usuário ao PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Copiar o arquivo de dependências
COPY --chown=appuser:appuser requirements.txt .

# Instalar as dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código da aplicação
COPY --chown=appuser:appuser . .

# Expõe a porta que o Uvicorn irá usar
EXPOSE 8000

# Comando para executar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
