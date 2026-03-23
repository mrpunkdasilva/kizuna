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

@app.get("/")
async def root():
    return {"message": "Kizuna Copilot Scrapper API is up and running!"}

@app.post("/scrape-job/", response_model=ScrapedJobData)
async def scrape_job(job_url: JobURL):
    """
    Usa wget para baixar o HTML, limpa o conteúdo e usa o Ollama para extrair o nome da vaga.
    """
    ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    model = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")

    try:
        # 1. Usar wget para baixar o conteúdo HTML
        # Usamos um User-Agent comum para evitar bloqueios simples
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        cmd = [
            "wget",
            "-qO-",  # Saída para stdout
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

        # 2. Limpar o HTML para economizar tokens (remover scripts, estilos, etc.)
        soup = BeautifulSoup(html_content, 'html.parser')
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        
        # Pegar apenas o texto visível ou partes relevantes se necessário, 
        # mas para o título o texto limpo geralmente basta.
        clean_text = soup.get_text(separator=' ', strip=True)
        # Limitar o tamanho do texto para não exceder limites de contexto da LLM
        clean_text = clean_text[:4000] 

        # 3. Chamar o Ollama para extrair o título em JSON
        prompt = (
            "Extract the job title from the following job posting text. "
            "Return the answer in JSON format with the key 'title'. "
            "If you cannot find it, return null.\n\n"
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
                    "stream": False
                },
                timeout=60.0
            )

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Erro no Ollama: {response.text}")

            ollama_result = response.json()
            try:
                # O Ollama retorna a resposta no campo 'response' quando format=json é usado
                data = json.loads(ollama_result.get("response", "{}"))
                return ScrapedJobData(title=data.get("title"))
            except (json.JSONDecodeError, KeyError):
                return ScrapedJobData(title=None)

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Tempo esgotado ao tentar baixar a página.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no scrapper: {str(e)}")
