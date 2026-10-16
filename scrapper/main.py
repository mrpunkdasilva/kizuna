import os
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
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    max_chars = int(os.getenv("SCRAPER_MAX_CHARS", "4000"))

    response_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "company": {"type": "string"},
            "location": {"type": "string"},
            "work_style": {"type": "string"},
            "employment_type": {"type": "string"},
            "seniority": {"type": "string"},
            "salary": {"type": "string"},
            "description": {"type": "string"},
            "requirements": {"type": "array", "items": {"type": "string"}},
            "benefits": {"type": "array", "items": {"type": "string"}},
            "tech_stack": {"type": "array", "items": {"type": "string"}},
            "soft_skills": {"type": "array", "items": {"type": "string"}},
            "interview_tips": {"type": "array", "items": {"type": "string"}},
            "ats_keywords": {"type": "array", "items": {"type": "string"}},
            "compatibility_score": {"type": "integer", "minimum": 0, "maximum": 100},
            "ai_summary": {"type": "string"},
        },
        "required": [
            "title", "company", "location", "work_style", "employment_type",
            "seniority", "description", "requirements", "benefits", "tech_stack",
            "soft_skills", "interview_tips", "ats_keywords", "compatibility_score",
            "ai_summary",
        ],
    }

    try:
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        print(f"Iniciando download da vaga: {job_url.url}")

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=60.0,
            headers={"User-Agent": user_agent},
        ) as client:
            page = await client.get(str(job_url.url))
            page.raise_for_status()
            raw_content = page.text

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
        clean_text = clean_text[:max_chars] # Texto reduzido para acelerar a inferência

        prompt = (
            "Você é a Kizuna, uma assistente que analisa vagas de tecnologia para o candidato.\n"
            "Leia o TEXTO DA VAGA e produza um overview claro e útil.\n"
            "Responda APENAS com um JSON válido, em português, sem markdown.\n\n"
            "Como preencher cada campo:\n"
            "- title: o cargo exatamente como anunciado.\n"
            "- company: nome da empresa (ou \"Não informado\").\n"
            "- location: cidade/estado ou país. Se exigir mudança de país, indique (ex.: \"Dubai (relocation)\"); se for 100% remoto, use \"Remoto\".\n"
            "- work_style: Remoto, Híbrido ou Presencial (coerente com a location).\n"
            "- employment_type: CLT, PJ ou Full-time.\n"
            "- seniority: Estágio, Junior, Pleno ou Senior (use pistas do texto como \"júnior\" ou anos de experiência).\n"
            "- salary: faixa salarial se aparecer; senão \"Não informado\".\n"
            "- description: 2 frases objetivas (máx. 40 palavras) sobre o dia a dia da vaga.\n"
            "- requirements: até 6 requisitos objetivos.\n"
            "- benefits: até 6 benefícios oferecidos (ex.: plano de saúde, moradia, visto, bônus).\n"
            "- tech_stack: até 8 tecnologias/ferramentas citadas.\n"
            "- soft_skills: até 5 habilidades COMPORTAMENTAIS (ex.: comunicação, trabalho em equipe). NÃO inclua tecnologias.\n"
            "- interview_tips: 3 dicas práticas de preparação, no imperativo (ex.: \"Revise hooks do React\"). IGNORE frases de marketing ou chamadas para ação da página.\n"
            "- ats_keywords: até 8 termos técnicos/competências-chave que um recrutador buscaria (derive de tech_stack e requirements).\n"
            "- compatibility_score: número de 0 a 100 (ex.: \"85\") de alinhamento com a vaga.\n"
            "- ai_summary: 2 a 3 frases (máx. 60 palavras) resumindo a oportunidade para o candidato.\n"
            "- Se a informação não estiver no texto, use \"Não informado\".\n\n"
            f"TEXTO DA VAGA:\n{clean_text}"
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
                    "format": response_schema,
                    "options": {
                        "num_ctx": 4096,
                        "num_predict": 700,
                        "num_thread": int(os.getenv("OLLAMA_NUM_THREAD", "10")),
                        "temperature": 0.1
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

        # Sanitiza o compatibility_score para garantir um número de 0 a 100
        score = str(final_data.get("compatibility_score", "")).strip()
        score_match = re.search(r'\d{1,3}', score)
        if score_match and 0 <= int(score_match.group()) <= 100:
            final_data["compatibility_score"] = score_match.group()
        else:
            final_data["compatibility_score"] = "Não informado"

        # Remove itens duplicados das listas (mantendo a ordem e ignorando maiúsculas)
        for field in ["requirements", "benefits", "tech_stack", "soft_skills", "interview_tips", "ats_keywords"]:
            items = final_data.get(field)
            if isinstance(items, list):
                seen = set()
                unique = []
                for item in items:
                    key = str(item).strip().lower()
                    if key and key not in seen:
                        seen.add(key)
                        unique.append(item)
                final_data[field] = unique or ["Não informado"]

        job_data = ScrapedJobData(**final_data)
        
        # Salva o último para debug
        with open("last_scraped_job.json", "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        
        return job_data
