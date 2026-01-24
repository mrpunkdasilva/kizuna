from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

app = FastAPI(
    title="Kizuna Copilot API",
    description="API para extrair e processar dados de vagas de emprego.",
    version="0.1.0",
)


class JobURL(BaseModel):
    url: HttpUrl


@app.get("/")
async def root():
    """Endpoint raiz para verificar se a API está no ar."""
    return {"message": "Kizuna Copilot API está no ar!"}


@app.post("/scrape-job/")
async def scrape_job(job_url: JobURL):
    """
    Endpoint para receber a URL de uma vaga, extrair os dados e retorná-los.
    (A lógica de scraping será implementada aqui)
    """
    # Placeholder para a lógica de scraping
    return {"status": "recebido", "url": job_url.url}

