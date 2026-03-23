import httpx
import asyncio
import json
import os
import traceback
from bs4 import BeautifulSoup

async def test_ollama_with_html():
    # Configurações
    ollama_host = "http://127.0.0.1:11434"
    model = "deepseek-r1:1.5b"
    html_path = "debug.html"
    
    if not os.path.exists(html_path):
        html_path = "../debug.html"
        if not os.path.exists(html_path):
            print(f"Erro: Arquivo debug.html não encontrado!")
            return

    print(f"Lendo o arquivo {html_path}...")
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        data = json.loads(content)
        if isinstance(data, dict) and 'html' in data:
            print("Detectado formato JSON, extraindo conteúdo do campo 'html'...")
            html_content = data['html']
        else:
            html_content = content
    except json.JSONDecodeError:
        html_content = content

    soup = BeautifulSoup(html_content, 'html.parser')
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    
    clean_text = soup.get_text(separator=' ', strip=True)
    clean_text = clean_text[:2000] # Reduzindo um pouco mais para ajudar a CPU

    print(f"Texto extraído (primeiros 100 caracteres): {clean_text[:100]}...")

    prompt = (
        "Extract the job title from the following job posting text. "
        "Return ONLY the answer in JSON format with the key 'title'. "
        "Do not include your thinking process, just the JSON.\n\n"
        f"Text: {clean_text}\n\n"
        "JSON Response:"
    )

    print(f"\nVerificando conexão com o Ollama em {ollama_host}...")
    
    try:
        # Timeout ILIMITADO para ver se o Ollama responde eventualmente
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                check = await client.get(f"{ollama_host}/api/tags")
                print(f"Conexão OK! Status: {check.status_code}")
            except Exception as e:
                print(f"FALHA NA CONEXÃO INICIAL: {e}")
                return

            print(f"Enviando prompt para o modelo {model}... (Estou sendo MUITO paciente agora!)")
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
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                try:
                    data = json.loads(result.get("response", "{}"))
                    print("\n--- Resultado da LLM ---")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    print("------------------------")
                except json.JSONDecodeError:
                    print("\n--- Resposta Bruta (Não é um JSON válido) ---")
                    print(result.get("response"))
                    print("---------------------------------------------")
            else:
                print(f"Erro no Ollama: {response.status_code} - {response.text}")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama_with_html())
