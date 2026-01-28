import os
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions

app = FastAPI(
    title="Kizuna Copilot API",
    description="API para extrair e processar dados de vagas de emprego.",
    version="0.2.0",
)


class JobURL(BaseModel):
    url: HttpUrl


class ScrapedJobData(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    description: str | None = None


@app.get("/")
async def root():
    """Endpoint raiz para verificar se a API está no ar."""
    return {"message": "Kizuna Copilot API is up and running!"}


@app.post("/scrape-job/", response_model=ScrapedJobData)
async def scrape_job(job_url: JobURL):
    """
    Endpoint para receber a URL de uma vaga, extrair os dados e retorná-los usando Selenium.
    """
    selenium_hub_url = os.getenv("SELENIUM_HUB_URL")
    if not selenium_hub_url:
        raise HTTPException(status_code=500, detail="SELENIUM_HUB_URL environment variable not set.")

    options = FirefoxOptions()
    options.add_argument("--headless")
    
    driver = None
    try:
        driver = webdriver.Remote(
            command_executor=selenium_hub_url,
            options=options
        )
        
        driver.get(str(job_url.url))
        
        driver.implicitly_wait(10)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # --- Novos seletores identificados ---
        title = soup.find('h1', class_='top-card-layout__title')
        company_elem = soup.find('a', class_='topcard__org-name-link')
        location_elem = soup.find('span', class_='topcard__flavor--bullet')
        description_div = soup.find('div', class_='description__text')

        extracted_data = {
            "title": title.get_text(strip=True) if title else None,
            "company": company_elem.get_text(strip=True) if company_elem else None,
            "location": location_elem.get_text(strip=True) if location_elem else None,
            "description": description_div.get_text(strip=True) if description_div else None,
        }

        return ScrapedJobData(**extracted_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during scraping: {e}")
    finally:
        if driver:
            driver.quit()