# Prompt: Analyze Job Description

## Context
Você recebeu o texto bruto de uma descrição de vaga de emprego extraído via web scraping. Sua tarefa é decompor este texto em categorias estruturadas para facilitar o matchmaking com o perfil do candidato.

## Instructions
1. Leia atentamente a descrição da vaga.
2. Identifique as tecnologias obrigatórias (Hard Skills).
3. Identifique as competências desejáveis ou diferenciais.
4. Extraia as principais responsabilidades do cargo.
5. Identifique o nível de senioridade e o modelo de trabalho (Remoto, Híbrido, Presencial).

## Structured Output (JSON)
Por favor, retorne **apenas** um objeto JSON seguindo este esquema:

```json
{
  "job_title": "string",
  "company": "string",
  "seniority": "string",
  "work_model": "string",
  "hard_skills": ["string"],
  "soft_skills": ["string"],
  "main_responsibilities": ["string"],
  "required_experience_years": number | null,
  "top_3_priorities": ["string"]
}
```

## Input Data
[TEXTO DA VAGA AQUI]
