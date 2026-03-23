import pytest
from unittest.mock import MagicMock, patch
import json
import subprocess
from main import app, JobURL, ScrapedJobData

MOCK_HTML = "<html><body><h1>Software Engineer</h1></body></html>"
MOCK_OLLAMA_RESPONSE = {
    "response": json.dumps({"title": "Software Engineer"})
}

@pytest.fixture
def mock_wget():
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(
            returncode=0,
            stdout=MOCK_HTML,
            stderr=""
        )
        yield mock

@pytest.fixture
def mock_ollama():
    with patch("httpx.AsyncClient.post") as mock:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_OLLAMA_RESPONSE
        mock.return_value = mock_response
        yield mock

@pytest.mark.asyncio
async def test_scrape_job_success(mock_wget, mock_ollama):
    # Precisamos importar e rodar a função diretamente ou usar o TestClient
    from main import scrape_job
    job_url = JobURL(url="https://example.com/job")
    
    result = await scrape_job(job_url)
    
    assert result.title == "Software Engineer"
    mock_wget.assert_called_once()
    mock_ollama.assert_called_once()

@pytest.mark.asyncio
async def test_scrape_job_wget_error(mock_ollama):
    with patch("subprocess.run") as mock_wget_err:
        mock_wget_err.return_value = MagicMock(
            returncode=1,
            stderr="404 Not Found"
        )
        from main import scrape_job, HTTPException
        job_url = JobURL(url="https://example.com/job")
        
        with pytest.raises(HTTPException) as exc:
            await scrape_job(job_url)
        assert exc.value.status_code == 500
        assert "Erro ao baixar a página" in exc.value.detail
