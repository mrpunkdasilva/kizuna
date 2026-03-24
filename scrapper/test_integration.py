import asyncio
import json
import os
import time
from unittest.mock import patch, MagicMock
from main import scrape_job, JobURL

async def test_ollama_integration():
    """
    Teste de integração que utiliza a lógica real do main.py
    mas simula o download do HTML usando o arquivo debug.html local.
    """
    html_path = "debug.html"
    if not os.path.exists(html_path):
        html_path = "../debug.html"
    
    if not os.path.exists(html_path):
        print(f"Erro: Arquivo {html_path} não encontrado!")
        return

    print(f"📖 Lendo o arquivo local: {html_path}...")
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        # Tenta carregar como JSON (caso o debug.html seja o dump da API)
        data = json.loads(content)
        html_content = data.get('html', content)
    except json.JSONDecodeError:
        html_content = content

    # Mock do subprocess.run (wget) para retornar o conteúdo do debug.html
    # Assim testamos toda a lógica de limpeza, prompt e chamada da IA no main.py
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=html_content,
            stderr=""
        )
        
        # O host do Ollama no ambiente local
        os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"
        
        print("🚀 Iniciando extração via scrape_job (main.py)...")
        print("---")
        
        start_time = time.perf_counter()
        
        # Chamada real da função que está no seu main.py
        job_url = JobURL(url="https://www.linkedin.com/jobs/view/test-integration")
        result = await scrape_job(job_url)
        
        end_time = time.perf_counter()
        
        print("---")
        print(f"✅ Teste concluído com sucesso!")
        print(f"⏱️  Tempo total de resposta: {end_time - start_time:.2f}s")
        
        if os.path.exists("last_scraped_job.json"):
            print(f"💾 O arquivo 'last_scraped_job.json' foi atualizado.")
        
        print("\n--- Verificação de Campos ---")
        fields = [
            "title", "company", "location", "work_style", "employment_type", 
            "seniority", "salary", "description", "requirements", 
            "benefits", "posted_at", "applications_count"
        ]
        for field in fields:
            value = getattr(result, field, "N/A")
            print(f"🔹 {field.replace('_', ' ').title()}: {value}")

if __name__ == "__main__":
    asyncio.run(test_ollama_integration())
