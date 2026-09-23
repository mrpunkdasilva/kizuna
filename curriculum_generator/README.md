# Curriculum Generator

Gerador de currículos dinâmicos em LaTeX + Jinja2 + xelatex.

## Arquitetura

```
curriculum_generator/
├── generate_cv.py           # Pipeline principal
├── data/
│   ├── curriculum_base.json     # Dados mestres (imutáveis)
│   └── jobs/
│       └── <job_slug>.json      # Override específico da vaga
├── templates/
│   ├── template_singlepage.tex   # Template principal (funciona, sem deps)
│   ├── template.tex              # Base Rezume adaptado
│   ├── template_ptbr.tex         # Versão PT-BR do Rezume
│   └── template_moderncv.tex     # Experimental (precisa fontawesome6)
└── debug*.tex                    # Artefatos de debug
```

## Como funciona

1. **curriculum_base.json** — Dados imutáveis: pessoal, experiências, skills, projetos, formação, idiomas
2. **jobs/<slug>.json** — Override por vaga: `summary`, `featured_projects`, `skills_priority`, `ats_keywords`
3. **Merge** — Python faz deep merge (base + job override)
4. **Render** — Jinja2 preenche `template_singlepage.tex`
5. **Compile** — xelatex (2 passes) → PDF

## Uso

```bash
# Gerar PDF para uma vaga
python3 generate_cv.py \
  --template templates/template_singlepage.tex \
  --base data/curriculum_base.json \
  --job data/jobs/eight_vision.json \
  --output-dir ../output \
  --name "Gustavo_Henrique_de_Jesus_da_Silva"

# Output: ../output/curriculo_Gustavo_Henrique_de_Jesus_da_Silva_eight_vision.pdf
```

## Para nova vaga

```bash
# 1. Copiar template de job
cp data/jobs/eight_vision.json data/jobs/nova_empresa.json

# 2. Editar campos específicos da vaga
# - summary: resumo customizado para a vaga
# - featured_projects: lista de IDs dos projetos em destaque (refs do curriculum_base.json)
# - skills_priority: ordem de prioridade das skills (opcional)
# - ats_keywords: keywords para ATS (opcional)

# 3. Gerar PDF
python3 generate_cv.py \
  --template templates/template_singlepage.tex \
  --base data/curriculum_base.json \
  --job data/jobs/nova_empresa.json \
  --output-dir ../output \
  --name "Gustavo_Henrique_de_Jesus_da_Silva"
```

## Schema: curriculum_base.json

```json
{
  "personal": { "name", "phone", "location", "email", "links": { "linkedin", "github", "tabnews", "devto" } },
  "experiences": [{ "title", "company", "period", "location", "bullets": [] }],
  "education": [{ "title", "institution", "period" }],
  "skills": { "Frontend": [], "Backend e APIs": [], "Bancos de Dados": [], "DevOps e Ferramentas": [], "Metodologias e Princípios": [] },
  "all_projects": { "<id>": { "title", "tech_stack": [], "highlights": [], "github", "demo" } },
  "languages": [{ "language", "level" }]
}
```

## Schema: jobs/<slug>.json

```json
{
  "job_slug": "eight_vision",
  "company": "Eight Vision",
  "position": "Desenvolvedor(a) Front-end Júnior",
  "summary": "Resumo customizado para a vaga...",
  "featured_projects": ["cybernews", "opala_filmes", "doces_da_thay", "blood_donation"],
  "skills_priority": ["React", "Next.js", "TypeScript", "Tailwind CSS", "Firebase", "Git"],
  "ats_keywords": ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Next.js", "Git", "APIs", "Responsividade", "Componentização"]
}
```

## Template: template_singlepage.tex

Template LaTeX custom (standalone, sem dependências problemáticas):
- Fonte: Latin Modern, 9pt
- Margens: 1.5cm (laterais), 1cm (topo/base)
- Ícones: símbolos Unicode + `\underline` para links
- Seções: Resumo, Experiência, Projetos, Formação, Habilidades, Idiomas
- Saída: 2 páginas A4 otimizadas

## Dependências

- Python 3.8+ com `jinja2`
- TeX Live com: `moderncv`, `fontawesome6`, `academicons`, `microtype`, `multirow`, `titlesec`, `enumitem`, `geometry`, `hyperref`, `xcolor`, `lmodern`, `ragged2e`, `soul` (opcional)

## Output naming

`curriculo_Gustavo_Henrique_de_Jesus_da_Silva_{job_slug}.pdf`