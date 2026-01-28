# Usar uma imagem base oficial do Python
FROM python:3.11-slim

# Variáveis de ambiente para a versão do geckodriver
ENV GECKODRIVER_VERSION=v0.34.0

# Instalar dependências do sistema, Firefox ESR e ferramentas necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    tar \
    ca-certificates \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

# Baixar, extrair e instalar o geckodriver
RUN wget --no-verbose -O /tmp/geckodriver.tar.gz "https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz" \
    && tar -C /usr/local/bin -xzf /tmp/geckodriver.tar.gz \
    && rm /tmp/geckodriver.tar.gz \
    && chmod +x /usr/local/bin/geckodriver

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

