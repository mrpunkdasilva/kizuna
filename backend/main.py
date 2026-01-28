import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

app = FastAPI(
    title="Kizuna Copilot API",
    description="API para extrair e processar dados de vagas de emprego.",
    version="0.1.0",
)


class JobURL(BaseModel):
    url: HttpUrl


class ScrapedJobData(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    description: str | None = None
    # Add other fields as needed


@app.get("/")
async def root():
    """Endpoint raiz para verificar se a API está no ar."""
    return {"message": "Kizuna Copilot API is up and running!"}


@app.post("/scrape-job/", response_model=ScrapedJobData)
async def scrape_job(job_url: JobURL):
    """
    Endpoint para receber a URL de uma vaga, extrair os dados e retorná-los.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(str(job_url.url), headers=headers)
        response.raise_for_status()  # Levanta um erro HTTP para status de erro (4xx ou 5xx)

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Lógica de extração de dados do LinkedIn ---
        # Estes seletores podem precisar de ajustes se o LinkedIn mudar sua estrutura HTML.
        # title = soup.find('h1', class_='topcard__title')
        # company = soup.find('a', class_='topcard__org-name-link')
        # location = soup.find('span', class_='topcard__flavor topcard__flavor--bullet')
        # description_div = soup.find('div', class_='description__text description__text--rich')

        # Updated selectors for LinkedIn based on current observation (Jan 2026)
        title = soup.find('p', class_='d6702861 e4111e1d _655037c4 _185fef28 aedc8401 b90d48f3 bc8cf9c8 _903d2b03 _2ad2a80d')
        company_elem = soup.find('a', class_='job-details-jobs-unified-top-card__company-name')
        location_elem = soup.find('span', class_='job-details-jobs-unified-top-card__job-location')
        description_div = soup.find('p', class_='d6702861 _06170c11 _655037c4 _185fef28 d065caac df5b4656 bc8cf9c8 _903d2b03 _2ad2a80d')

        extracted_data = {
            "title": title.get_text(strip=True) if title else None,
            "company": company_elem.get_text(strip=True) if company_elem else None,
            "location": location_elem.get_text(strip=True) if location_elem else None,
            "description": description_div.get_text(strip=True) if description_div else None,
        }

        return ScrapedJobData(**extracted_data)

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error fetching URL: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during scraping: {e}")