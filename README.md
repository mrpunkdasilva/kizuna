<p align="center">
<img src="./.vsc/kizuna.svg" alt="Kizuna Iporá" width="200px">
</p>

# Kizuna Copilot

> *A mascote e guia do projeto é a **Kizuna Iporá**.*

## Visão Geral

O **Kizuna Copilot** é uma solução para otimizar a criação de currículos personalizados, utilizando uma arquitetura de microsserviços. Ele é composto por um serviço de web scraping em Python, um backend principal em Spring Boot para orquestração e interação com modelos de linguagem de grande escala (LLMs) via Ollama.

## Arquitetura de Microsserviços

O projeto é dividido nos seguintes serviços principais:

1.  **Ollama (`ollama`):**
    *   Responsável por hospedar e gerenciar os modelos de linguagem de grande escala (LLMs) para processamento e geração de conteúdo.

2.  **Python Scraper (`python-scraper`):**
    *   Um serviço FastAPI em Python dedicado à extração de informações de vagas de emprego de plataformas como o LinkedIn.
    *   Expõe um endpoint REST para receber URLs de vagas e retornar os dados brutos extraídos.
    *   Porta exposta: `8000`.

3.  **Spring Boot Backend (`springboot-app`):**
    *   O backend principal da aplicação, construído com Spring Boot em Java.
    *   Será responsável por orquestrar as chamadas ao serviço Python Scraper, interagir com o Ollama para adaptar o conteúdo e expor a API final para o cliente.
    *   Porta exposta: `8080`.

## Funcionalidades (Planejadas)

*   **Web Scraping Inteligente:** Extração de informações relevantes de links de vagas de emprego (implementado no `python-scraper`).
*   **Geração de Conteúdo com LLM:** Utilização de inteligência artificial para adaptar e otimizar o texto do seu currículo com base nos requisitos da vaga (orquestrado pelo `springboot-app` com `ollama`).
*   **API de Orquestração:** Exposição de endpoints para gerenciar o processo de adaptação de currículos (no `springboot-app`).
*   **Formato Markdown e PDF:** Geração final de currículos em Markdown e conversão para PDF.

## Pré-requisitos

Certifique-se de ter o Docker e o Docker Compose (com a nova sintaxe `docker compose`) instalados em seu sistema.

## Como Usar

Para iniciar e interagir com o Kizuna Copilot, siga os passos abaixo:

### 1. Iniciar os Serviços

No diretório raiz do projeto, execute o comando para construir as imagens e iniciar todos os serviços em segundo plano:

```bash
docker compose up --build -d
```

Este comando irá:
*   Baixar a imagem do Ollama.
*   Construir a imagem do `python-scraper` (FastAPI).
*   Construir a imagem do `springboot-app` (Spring Boot), instalando OpenJDK e Maven.
*   Iniciar todos os contêineres.

### 2. Baixar o Modelo LLM (Ollama)

Após os contêineres estarem rodando, baixe o modelo `deepseek-llm:7b` para o Ollama. Este modelo será usado para a geração de conteúdo. Este passo é essencial para a funcionalidade de IA.

```bash
docker exec ollama ollama pull deepseek-llm:7b
```
Aguarde o download ser concluído.

### 3. Verificar o Status dos Serviços

Você pode verificar o status dos contêineres com:

```bash
docker compose ps
```

### 4. Testar os Endpoints Básicos

*   **Python Scraper (FastAPI):**
    ```bash
    curl http://localhost:8000/
    ```
    Saída esperada: `{"message":"Kizuna Copilot API está no ar!"}`

*   **Spring Boot Backend:**
    ```bash
    curl http://localhost:8080/
    ```
    Saída esperada (um erro 404, pois ainda não há endpoints definidos além do padrão): `{"timestamp":"...","status":404,"error":"Not Found","path":"/"}`

### 5. Parar os Serviços

Quando terminar de usar, você pode parar e remover os contêineres:
```bash
docker compose down
```

## Desenvolvimento

Este projeto está em desenvolvimento contínuo.

## Estrutura do Projeto

*   `backend/`: Contém a aplicação Python FastAPI para web scraping.
    *   `main.py`: Lógica da API FastAPI.
    *   `Dockerfile`: Instruções para construir a imagem Docker do scraper.
    *   `requirements.txt`: Dependências Python.
*   `springboot-app/`: Contém a aplicação Spring Boot principal.
    *   `pom.xml`: Configurações Maven e dependências Java.
    *   `src/`: Código fonte Java e recursos.
    *   `Dockerfile`: Instruções para construir a imagem Docker do backend.
*   `docker-compose.yml`: Arquivo de orquestração do Docker Compose para todos os serviços.
*   `data/`: Diretório para dados de entrada (JSONs de currículos, etc.).
*   `curriculums/`: Diretório para os currículos gerados em Markdown.
*   `output/`: Diretório para os currículos gerados em PDF.

## Contato

Para mais informações, entre em contato com [email](email) ou [dc](dc)
