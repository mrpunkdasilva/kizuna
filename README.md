<p align="center">
<img src="./.vsc/kizuna.svg" alt="Kizuna Copilot" width="200px">
</p>

# Kizuna Copilot

> *A mascote e guia do meu projeto pessoal é a **Kizuna Iporá**.*

## Visão Geral

O **Kizuna Copilot** é uma solução completa para otimizar a criação de currículos personalizados, utilizando uma arquitetura moderna de microsserviços. O sistema automatiza a extração de dados de vagas de emprego, utiliza Inteligência Artificial para adaptar o conteúdo do currículo e gera versões finais em PDF, tudo isso com monitoramento em tempo real.

## Arquitetura do Sistema

O projeto é orquestrado via Docker e dividido nos seguintes serviços:

1.  **Frontend (`vue-client`):**
    *   Interface web construída com **Vue.js** e **Vite**.
    *   Permite interagir com o sistema de forma amigável.
    *   Porta exposta: `3000`.

2.  **Backend Principal (`springboot-app`):**
    *   O coração do sistema, desenvolvido em **Java com Spring Boot**.
    *   Gerencia a persistência de dados no MongoDB, orquestra as chamadas de IA e gera os PDFs.
    *   Porta exposta: `8080`.

3.  **Python Scraper (`python-scraper`):**
    *   Serviço especializado em extração de dados (Web Scraping) construído com **FastAPI**.
    *   Focado em coletar descrições de vagas dinamicamente.
    *   Porta exposta: `8000`.

4.  **Inteligência Artificial (`ollama`):**
    *   Hospeda o modelo **DeepSeek R1 (1.5B)** localmente.
    *   Utilizado para analisar vagas e reescrever seções do currículo.
    *   Um serviço auxiliar (`ollama-pull-model`) garante que o modelo seja baixado automaticamente ao subir o sistema.

5.  **Banco de Dados (`mongo`):**
    *   Utiliza **MongoDB** para armazenar as informações de currículos e vagas processadas.

6.  **Observabilidade (`prometheus` & `grafana`):**
    *   **Prometheus:** Coleta métricas de desempenho dos serviços. (Porta `9090`)
    *   **Grafana:** Dashboard visual para monitorar a saúde do sistema. (Porta `3001`)

## Funcionalidades

*   **Extração Inteligente:** Captura detalhes de vagas diretamente de links do LinkedIn.
*   **Adaptação com IA:** O modelo DeepSeek ajusta seu resumo e experiências para dar "match" com a vaga.
*   **Gestão de Dados:** Armazena suas experiências, projetos e habilidades de forma estruturada.
*   **Geração de PDF:** Exporta o currículo finalizado e otimizado em um formato profissional.
*   **Monitoramento:** Acompanhe o consumo de recursos e requisições via Dashboards.

## Pré-requisitos

*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

## Como Executar

É super simples! Com um único comando você sobe todo o ecossistema:

### 1. Subir o Sistema

No diretório raiz, execute:

```bash
docker compose up -d
```

Isso vai:
1.  Iniciar o banco de dados e as ferramentas de monitoramento.
2.  Subir o Ollama e baixar o modelo DeepSeek R1 (pode demorar um pouco na primeira vez).
3.  Compilar e rodar a API Spring Boot e o Scraper Python.
4.  Lançar o Frontend Vue.js.

### 2. Acessar os Serviços

*   **Frontend:** [http://localhost:3000](http://localhost:3000)
*   **API Backend (Spring Boot):** [http://localhost:8080](http://localhost:8080)
    *   **Swagger UI:** [http://localhost:8080/swagger-ui.html](http://localhost:8080/swagger-ui.html)
*   **Scraper API (FastAPI):** [http://localhost:8000](http://localhost:8000)
    *   **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Grafana:** [http://localhost:3001](http://localhost:3001) (Usuário: `admin` / Senha: `admin`)

### 3. Verificar Saúde do Sistema

```bash
docker compose ps
```

## Estrutura de Pastas

*   `api/`: Código fonte do Backend Java (Spring Boot).
*   `client/`: Código fonte do Frontend (Vue.js).
*   `scrapper/`: Script de scraping em Python (FastAPI).
*   `data/`: Arquivos JSON base com suas informações profissionais.
*   `curriculums/`: Onde os currículos adaptados (`.md`) são armazenados.
*   `output/`: Onde os PDFs finais são gerados.
*   `kizuna-kokoro/`: Prompts e "skills" da IA para o processo de otimização.

## Desenvolvimento e Testes

### Executar Testes (Backend)
```bash
docker exec springboot_app mvn test
```

### Executar Testes (Scraper)
```bash
docker exec python_scraper pytest
```

---
*Este é um projeto pessoal em constante evolução. Sinta-se à vontade para explorar e aprender com a estrutura!*
