import asyncio
import json
import os
import time
import pytest
from unittest.mock import patch, MagicMock
from main import scrape_job, JobURL

@pytest.mark.asyncio
async def test_ollama_integration():
    """
    Teste de integração que utiliza a lógica real do main.py
    mas simula o download do HTML usando o arquivo debug.html local.
    """
    # Busca o arquivo na raiz do projeto ou no diretório atual
    possible_paths = [
        "debug.html",
        "../debug.html",
        os.path.join(os.path.dirname(__file__), "..", "debug.html")
    ]
    
    html_path = None
    for path in possible_paths:
        if os.path.exists(path):
            html_path = path
            break
    
    if not html_path:
        print(f"Erro: Arquivo debug.html não encontrado nos caminhos: {possible_paths}!")
        return

    print(f"📖 Lendo o arquivo local: {html_path}...")
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        # Tenta carregar como JSON (caso o debug.html seja o dump da API)
        data = json.loads(content)
        html_content = data.get('html', content)
        print("💡 Conteúdo extraído do campo 'html' do JSON.")
    except json.JSONDecodeError:
        html_content = content
        print("💡 Conteúdo lido como HTML puro.")

    # Mock do subprocess.run no módulo 'main' para garantir que intercepte a chamada correta
    with patch("main.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=html_content,
            stderr=""
        )
        
        # O host do Ollama no ambiente local (ajuste se necessário)
        os.environ["OLLAMA_HOST"] = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        os.environ["OLLAMA_MODEL"] = "deepseek-r1:1.5b"
        
        print(f"🚀 Iniciando extração profunda via Kizuna AI usando modelo: {os.environ['OLLAMA_MODEL']}")
        print("---")
        
        start_time = time.perf_counter()
        
        # Chamada real da função que está no seu main.py
        # A URL é dummy pois o subprocess.run está mockado
        job_url = JobURL(url="https://www.linkedin.com/jobs/view/test-integration")
        result = await scrape_job(job_url)
        
        end_time = time.perf_counter()
        
        print("---")
        print(f"✅ Teste concluído com sucesso!")
        print(f"⏱️  Tempo total de resposta: {end_time - start_time:.2f}s")
        
        print("\n--- [RELATÓRIO COMPLETO DA KIZUNA] ---")
        
        # Lista completa de campos
        fields = [
            "title", "company", "location", "work_style", "employment_type", 
            "seniority", "salary", "posted_at", "applications_count",
            "tech_stack", "soft_skills", "pros", "cons", "interview_tips", 
            "ats_keywords", "compatibility_score", "company_values",
            "description", "requirements", "ai_summary"
        ]
        
        for field in fields:
            value = getattr(result, field, "N/A")
            label = field.replace('_', ' ').upper()
            print(f"📍 {label}: {value}")

if __name__ == "__main__":
    asyncio.run(test_ollama_integration())
