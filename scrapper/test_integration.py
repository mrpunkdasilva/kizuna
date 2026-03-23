import httpx
import asyncio
import json
import os
import time
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
            html_content = data['html']
        else:
            html_content = content
    except json.JSONDecodeError:
        html_content = content

    soup = BeautifulSoup(html_content, 'html.parser')
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    
    clean_text = soup.get_text(separator=' ', strip=True)
    clean_text = clean_text[:2000] 

    prompt = (
        "Extract the job title from the following job posting text. "
        "Return ONLY the answer in JSON format with the key 'title'. "
        "Do not include your thinking process, just the JSON.\n\n"
        f"Text: {clean_text}\n\n"
        "JSON Response:"
    )

    print(f"\nVerificando conexão com o Ollama em {ollama_host}...")
    
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                await client.get(f"{ollama_host}/api/tags")
            except Exception as e:
                print(f"FALHA NA CONEXÃO: {e}")
                return

            print(f"Enviando prompt para o modelo {model}... (Cronômetro iniciado!)")
            
            start_time = time.perf_counter() # Início da medição
            
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
            
            end_time = time.perf_counter() # Fim da medição
            duration = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Extraindo dados de performance do Ollama (vêm em nanossegundos)
                total_dur_ms = result.get("total_duration", 0) / 1e6
                load_dur_ms = result.get("load_duration", 0) / 1e6
                eval_count = result.get("eval_count", 0) # número de tokens gerados
                eval_dur_ms = result.get("eval_duration", 0) / 1e6
                
                tokens_per_sec = (eval_count / (eval_dur_ms / 1000)) if eval_dur_ms > 0 else 0

                try:
                    data = json.loads(result.get("response", "{}"))
                    print("\n--- Resultado da LLM ---")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    print("------------------------")
                except json.JSONDecodeError:
                    print("\n--- Resposta Bruta ---")
                    print(result.get("response"))
                
                print(f"\n📊 ANALYTICS SIMPLES:")
                print(f"⏱️  Tempo total (espera real): {duration:.2f}s")
                print(f"🧠 Tempo de processamento (Ollama): {total_dur_ms/1000:.2f}s")
                print(f"📦 Tempo de carga do modelo: {load_dur_ms/1000:.2f}s")
                print(f"⚡ Velocidade: {tokens_per_sec:.2f} tokens/s")
                print(f"📝 Tokens gerados: {eval_count}")
                print(f"------------------------")
                
            else:
                print(f"Erro no Ollama: {response.status_code} - {response.text}")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama_with_html())
