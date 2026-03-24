import os
import subprocess
import json
import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

app = FastAPI(
    title="Kizuna Copilot Scrapper API",
    description="API para extrair dados de vagas usando wget e Ollama.",
    version="1.0.0",
)

class JobURL(BaseModel):
    url: HttpUrl

class ScrapedJobData(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    work_style: str | None = None
    employment_type: str | None = None
    seniority: str | None = None
    salary: str | None = None
    description: str | None = None
    requirements: list[str] | None = None
    benefits: list[str] | None = None
    posted_at: str | None = None
    applications_count: str | None = None

@app.get("/")
async def root():
    return {"message": "Kizuna Copilot Scrapper API is up and running!"}

@app.post("/scrape-job/", response_model=ScrapedJobData)
async def scrape_job(job_url: JobURL):
    """
    Usa wget para baixar o HTML, limpa o conteúdo e usa o Ollama para extrair os detalhes da vaga.
    """
    ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    model = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")

    try:
        # 1. Usar wget para baixar o conteúdo HTML
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        cmd = [
            "wget",
            "-qO-",
            "--no-check-certificate",
            "--timeout=20",
            "--tries=2",
            f"--user-agent={user_agent}",
            str(job_url.url)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else "Erro desconhecido (verifique se a URL é válida)"
            raise HTTPException(status_code=500, detail=f"Erro ao baixar a página: {error_msg}")

        html_content = result.stdout

        # 2. Limpar o HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        
        clean_text = soup.get_text(separator=' ', strip=True)
        clean_text = clean_text[:4000] 

        # 3. Chamar o Ollama com o prompt completo
        prompt = (
            "Extract the following job information from the text below:\n"
            "- Job Title\n"
            "- Company Name\n"
            "- Location\n"
            "- Work Style (Remote, Hybrid, or On-site)\n"
            "- Employment Type (Full-time, Part-time, Contract, etc.)\n"
            "- Seniority Level\n"
            "- Salary/Compensation (if mentioned)\n"
            "- Job Description (summary)\n"
            "- Requirements (list)\n"
            "- Benefits (list)\n"
            "- Date Posted (e.g., '2 weeks ago')\n"
            "- Number of Applicants (if mentioned)\n\n"
            "Return ONLY a JSON object with the keys: 'title', 'company', 'location', 'work_style', 'employment_type', 'seniority', 'salary', 'description', 'requirements', 'benefits', 'posted_at', 'applications_count'.\n"
            "Do not include your thinking process, just the JSON.\n\n"
            f"Text: {clean_text}\n\n"
            "JSON Response:"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "num_ctx": 2048,
                        "temperature": 0.0
                    }
                },
                timeout=None
            )

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Erro no Ollama: {response.text}")

            ollama_result = response.json()
            try:
                raw_json = ollama_result.get("response", "{}")
                data = json.loads(raw_json)
                
                # Criar o objeto de resposta
                job_data = ScrapedJobData(**data)
                
                # Mostrar no terminal
                print("\n--- [SCRAPER] Job Data Extracted ---")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                print("------------------------------------\n")
                
                # Salvar em um arquivo JSON local (opcional, mas solicitado)
                with open("last_scraped_job.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                return job_data
            except (json.JSONDecodeError, KeyError, Exception) as e:
                print(f"Erro ao processar JSON da AI: {str(e)}")
                return ScrapedJobData()

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Tempo esgotado ao tentar baixar a página.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no scrapper: {str(e)}")
