import os
import subprocess
import json
import httpx
import re
import traceback
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Any

app = FastAPI(
    title="Kizuna Copilot Scrapper API",
    description="API para extrair dados de vagas usando wget e Ollama.",
    version="1.0.0",
)

class JobURL(BaseModel):
    url: HttpUrl
    language: str = "pt-br"

class ScrapedJobData(BaseModel):
    title: Any | None = None
    company: Any | None = None
    location: Any | None = None
    work_style: Any | None = None
    employment_type: Any | None = None
    seniority: Any | None = None
    salary: Any | None = None
    description: Any | None = None
    requirements: Any | None = None
    benefits: Any | None = None
    posted_at: Any | None = None
    applications_count: Any | None = None
    tech_stack: Any | None = None
    soft_skills: Any | None = None
    pros: Any | None = None
    cons: Any | None = None
    ai_summary: Any | None = None
    interview_tips: Any | None = None
    ats_keywords: Any | None = None
    compatibility_score: Any | None = None
    company_values: Any | None = None

@app.get("/")
async def root():
    return {"message": "Kizuna Copilot Scrapper API is up and running!"}

@app.post("/scrape-job/", response_model=ScrapedJobData)
async def scrape_job(job_url: JobURL):
    ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    model = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")

    try:
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        print(f"Iniciando download da vaga: {job_url.url}")
        cmd = [
            "wget", "-qO-", "--no-check-certificate", "--timeout=60", "--tries=3",
            f"--user-agent={user_agent}", str(job_url.url)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Erro no wget: {result.stderr}")
            raise HTTPException(status_code=500, detail="Erro ao baixar a página.")

        raw_content = result.stdout
        print(f"Página baixada com sucesso ({len(raw_content)} bytes). Processando conteúdo...")
        
        # Se o conteúdo for um JSON (comum em dumps de debug), extraímos o HTML dele
        try:
            json_data = json.loads(raw_content)
            html_content = json_data.get('html', raw_content)
        except:
            html_content = raw_content

        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove lixo para sobrar mais espaço para o texto útil
        for irrelevant in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "button", "input", "form"]):
            irrelevant.decompose()
        
        # Tenta pegar o texto de áreas comuns de vagas do LinkedIn
        main_content = soup.find('main') or soup.find('div', id='main-content') or soup.body
        
        if main_content:
            clean_text = main_content.get_text(separator=' ', strip=True)
        else:
            clean_text = soup.get_text(separator=' ', strip=True)
            
        # Limpa espaços excessivos
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        clean_text = clean_text[:10000] # Aumentado para 10k para garantir a descrição

        prompt = (
            "Analise detalhadamente a vaga abaixo e extraia as informações em formato JSON.\n"
            "Responda APENAS com o objeto JSON, sem explicações adicionais fora das tags <think>.\n\n"
            f"TEXTO DA VAGA:\n{clean_text}\n\n"
            "FORMATO JSON ESPERADO:\n"
            "{\n"
            "  \"title\": \"Título da vaga\",\n"
            "  \"company\": \"Nome da empresa\",\n"
            "  \"location\": \"Cidade/Estado\",\n"
            "  \"work_style\": \"Remoto/Híbrido/Presencial\",\n"
            "  \"employment_type\": \"CLT/PJ/Full-time\",\n"
            "  \"seniority\": \"Estágio/Junior/Pleno/Senior\",\n"
            "  \"salary\": \"Valor ou 'Não informado'\",\n"
            "  \"description\": \"Resumo detalhado das responsabilidades\",\n"
            "  \"requirements\": [\"lista de requisitos técnicos\"],\n"
            "  \"benefits\": [\"lista de benefícios\"],\n"
            "  \"tech_stack\": [\"tecnologias utilizadas\"],\n"
            "  \"soft_skills\": [\"habilidades comportamentais\"],\n"
            "  \"posted_at\": \"Tempo de publicação\",\n"
            "  \"applications_count\": \"Qtd de candidatos\",\n"
            "  \"pros\": [\"pontos positivos\"],\n"
            "  \"cons\": [\"desafios/pontos negativos\"],\n"
            "  \"interview_tips\": [\"dicas para entrevista\"],\n"
            "  \"ats_keywords\": [\"palavras-chave para currículo\"],\n"
            "  \"compatibility_score\": \"0-100%\",\n"
            "  \"company_values\": [\"cultura da empresa\"],\n"
            "  \"ai_summary\": \"Resumo executivo final\"\n"
            "}"
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no processamento da página: {str(e)}")

    print(f"Enviando para o Ollama (modelo: {model})...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_ctx": 12000, 
                        "temperature": 0.2
                    }
                },
                timeout=600 # Aumentado para 10 minutos
            )
            print("Resposta do Ollama recebida!")
        except Exception as e:
            print(f"Erro na chamada ao Ollama: {e}")
            raise HTTPException(status_code=500, detail=f"Erro no Ollama: {str(e)}")

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Erro no Ollama.")

        raw_response = response.json().get("response", "")
        
        # Remove o raciocínio do DeepSeek
        if "</think>" in raw_response:
            json_text = raw_response.split("</think>")[-1].strip()
        else:
            json_text = raw_response.strip()

        # Tenta extrair o JSON se o modelo colocou dentro de blocos de código
        json_match = re.search(r'```json\s*(.*?)\s*```', json_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        
        # Se não achou bloco de código, tenta achar o primeiro { e o último }
        else:
            json_match = re.search(r'(\{.*\})', json_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)

        try:
            data = json.loads(json_text)
        except Exception as e:
            print(f"Erro ao parsear JSON do Ollama: {e}\nResposta bruta: {json_text}")
            # Fallback para evitar erro 500
            data = {"title": "Erro no processamento da IA"}

        # Garante que todos os campos do modelo ScrapedJobData existam
        final_data = {}
        expected_fields = ScrapedJobData.model_fields.keys()
        
        for field in expected_fields:
            val = data.get(field)
            if val is None or val == "" or val == []:
                if "list" in str(ScrapedJobData.model_fields[field].annotation).lower() or field in ["requirements", "benefits", "tech_stack", "soft_skills", "pros", "cons", "interview_tips", "ats_keywords", "company_values"]:
                    final_data[field] = ["Não informado"]
                else:
                    final_data[field] = "Não informado"
            else:
                final_data[field] = val

        job_data = ScrapedJobData(**final_data)
        
        # Salva o último para debug
        with open("last_scraped_job.json", "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        
        return job_data
