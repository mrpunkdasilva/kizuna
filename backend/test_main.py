import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from pydantic import HttpUrl
from main import scrape_job, ScrapedJobData, app, JobURL
import os

# Mock HTML content for testing
MOCK_HTML_CONTENT = """
<html>
    <body>
        <h1 class="top-card-layout__title">Junior Web Developer</h1>
        <a class="topcard__org-name-link">Firegang Dental Marketing</a>
        <span class="topcard__flavor--bullet">United States</span>
        <div class="description__text">
            This is a detailed job description for a Junior Web Developer at Firegang.
        </div>
    </body>
</html>
"""

# Mock HTML content when no data is found
MOCK_HTML_NO_DATA = """
<html>
    <body>
        <h1>Some other title</h1>
        <p>Some other content</p>
    </body>
</html>
"""


@pytest.fixture
def mock_driver():
    """Fixture to mock the Selenium WebDriver."""
    with patch('main.webdriver.Remote') as mock_remote:
        mock_instance = MagicMock()
        mock_instance.page_source = MOCK_HTML_CONTENT
        mock_remote.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_driver_no_data():
    """Fixture to mock the Selenium WebDriver with no relevant data."""
    with patch('main.webdriver.Remote') as mock_remote:
        mock_instance = MagicMock()
        mock_instance.page_source = MOCK_HTML_NO_DATA
        mock_remote.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_env_vars():
    """Fixture to mock environment variables."""
    with patch.dict(os.environ, {"SELENIUM_HUB_URL": "http://mock-selenium-hub:4444/wd/hub"}):
        yield


@pytest.mark.asyncio
async def test_scrape_job_success(mock_driver, mock_env_vars):
    """Test successful scraping of a job page."""
    job_url = JobURL(url="https://www.linkedin.com/jobs/view/test-job-url")
    result = await scrape_job(job_url)

    assert result.title == "Junior Web Developer"
    assert result.company == "Firegang Dental Marketing"
    assert result.location == "United States"
    assert result.description == "This is a detailed job description for a Junior Web Developer at Firegang."
    mock_driver.get.assert_called_once_with(str(job_url.url))
    mock_driver.quit.assert_called_once()

@pytest.mark.asyncio
async def test_scrape_job_missing_env_var():
    """Test that an HTTPException is raised if SELENIUM_HUB_URL is not set."""
    # Temporarily clear the env var for this test
    with patch.dict(os.environ, {}, clear=True):
        job_url = JobURL(url="https://www.linkedin.com/jobs/view/test-job-url")
        with pytest.raises(HTTPException) as exc_info:
            await scrape_job(job_url)
        assert exc_info.value.status_code == 500
        assert "SELENIUM_HUB_URL environment variable not set." in exc_info.value.detail

@pytest.mark.asyncio
async def test_scrape_job_selenium_exception(mock_env_vars):
    """Test error handling when Selenium encounters an exception."""
    with patch('main.webdriver.Remote', side_effect=Exception("Selenium error")):
        job_url = JobURL(url="https://www.linkedin.com/jobs/view/test-job-url")
        with pytest.raises(HTTPException) as exc_info:
            await scrape_job(job_url)
        assert exc_info.value.status_code == 500
        assert "Error during scraping: Selenium error" in exc_info.value.detail

@pytest.mark.asyncio
async def test_scrape_job_no_data_found(mock_driver_no_data, mock_env_vars):
    """Test scraping when no data is found for the given selectors."""
    job_url = JobURL(url="https://www.linkedin.com/jobs/view/test-job-url")
    result = await scrape_job(job_url)

    assert result.title is None
    assert result.company is None
    assert result.location is None
    assert result.description is None
    mock_driver_no_data.get.assert_called_once_with(str(job_url.url))
    mock_driver_no_data.quit.assert_called_once()
