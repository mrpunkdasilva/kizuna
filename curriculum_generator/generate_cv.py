#!/usr/bin/env python3
"""
Curriculum Generator - LaTeX + JSON + Jinja2 + xelatex
Generates tailored PDF resumes for specific job applications.
"""

import json
import argparse
import subprocess
import sys
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


def load_json(filepath: Path) -> dict:
    """Load JSON file with UTF-8 encoding."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def clean_url(url: str) -> str:
    """Remove protocol from URL for LaTeX href."""
    return url.replace("https://", "").replace("http://", "")


def sanitize_for_latex_table(text: str) -> str:
    """Sanitize text for use in LaTeX table cells - keep & as-is for table column separators."""
    if not isinstance(text, str):
        text = str(text)
    return text


def merge_data(base: dict, job: dict) -> dict:
    """Merge base curriculum with job-specific overrides."""
    # Start with base data
    merged = base.copy()

    # Add cleaned URLs for personal links
    personal = merged.get('personal', {})
    links = personal.get('links', {})
    personal['linkedin_clean'] = clean_url(links.get('linkedin', ''))
    personal['github_clean'] = clean_url(links.get('github', ''))
    personal['tabnews_clean'] = clean_url(links.get('tabnews', ''))
    personal['devto_clean'] = clean_url(links.get('devto', ''))

    # Add job-specific fields
    merged['job'] = {
        'slug': job.get('job_slug', ''),
        'company': job.get('company', ''),
        'position': job.get('position', '')
    }
    merged['summary'] = job.get('summary', base.get('summary', ''))

    # Get featured projects from all_projects and add cleaned URLs
    featured_ids = job.get('featured_projects', [])
    all_projects = base.get('all_projects', {})
    featured_projects = []
    for pid in featured_ids:
        if pid in all_projects:
            proj = all_projects[pid].copy()
            proj['github_clean'] = clean_url(proj.get('github', ''))
            featured_projects.append(proj)
    merged['featured_projects'] = featured_projects

    # Add skills priority and ATS keywords if present
    if 'skills_priority' in job:
        merged['skills_priority'] = job['skills_priority']
    if 'ats_keywords' in job:
        merged['ats_keywords'] = job['ats_keywords']

    # Sanitize skills categories for LaTeX table (replace & with "and")
    if 'skills' in merged:
        sanitized_skills = {}
        for cat, skill_list in merged['skills'].items():
            sanitized_cat = sanitize_for_latex_table(cat)
            sanitized_skills[sanitized_cat] = skill_list
        merged['skills'] = sanitized_skills

    return merged


def render_template(template_path: Path, data: dict) -> str:
    """Render LaTeX template with Jinja2."""
    env = Environment(
        loader=FileSystemLoader(template_path.parent),
        autoescape=select_autoescape(),
        block_start_string='{%',
        block_end_string='%}',
        variable_start_string='[[',
        variable_end_string=']]',
        comment_start_string='[#',
        comment_end_string='#]',
        keep_trailing_newline=True
    )

# Custom filter to escape LaTeX special characters
    def escape_latex(text):
        if not isinstance(text, str):
            text = str(text)
        # Order matters: replace % before \ to avoid \% becoming \textbackslash{}%
        replacements = [
            ('%', r'\%'),
            ('$', r'\$'),
            ('#', r'\#'),
            ('_', r'\_'),
            ('{', r'\{'),
            ('}', r'\}'),
            ('~', r'\textasciitilde{}'),
            ('^', r'\textasciicircum{}'),
            ('&', r'\&'),
            ('\\', r'\textbackslash{}'),
        ]
        for char, escaped in replacements:
            text = text.replace(char, escaped)
        return text

    env.filters['escape_latex'] = escape_latex
    env.filters['e'] = escape_latex  # alias

    template = env.get_template(template_path.name)
    return template.render(**data)


def compile_latex(tex_path: Path, output_dir: Path, job_slug: str, full_name: str) -> Path:
    """Compile LaTeX to PDF using xelatex."""
    # Change to output directory for compilation
    original_cwd = os.getcwd()
    os.chdir(output_dir)

    try:
        # Copy .tex file to output directory with simple name
        tex_filename = f"curriculo_{full_name.replace(' ', '_')}_{job_slug}.tex"
        tex_output = output_dir / tex_filename

        with open(tex_output, 'w', encoding='utf-8') as f:
            with open(tex_path, 'r', encoding='utf-8') as src:
                f.write(src.read())

        # Run xelatex twice for proper references
        for i in range(2):
            result = subprocess.run(
                ['xelatex', '-interaction=nonstopmode', tex_filename],
                capture_output=True,
                text=True,
                timeout=120
            )
            # xelatex returns non-zero for warnings (overfull hbox, etc.) but still produces PDF
            # Check if PDF was created instead of relying on return code
            pdf_filename = tex_filename.replace('.tex', '.pdf')
            pdf_path = output_dir / pdf_filename
            if not pdf_path.exists():
                print(f"xelatex run {i+1} failed - no PDF generated:")
                print(result.stdout[-2000:] if result.stdout else "No stdout")
                print(result.stderr[-2000:] if result.stderr else "No stderr")
                raise RuntimeError(f"xelatex compilation failed (run {i+1}) - PDF not created")

        # Return PDF path
        pdf_filename = tex_filename.replace('.tex', '.pdf')
        return output_dir / pdf_filename

    finally:
        os.chdir(original_cwd)


def main():
    parser = argparse.ArgumentParser(description='Generate tailored PDF resume from LaTeX template')
    parser.add_argument('--template', required=True, help='Path to LaTeX template (.tex)')
    parser.add_argument('--base', required=True, help='Path to base curriculum JSON')
    parser.add_argument('--job', required=True, help='Path to job-specific JSON')
    parser.add_argument('--output-dir', required=True, help='Output directory for PDF')
    parser.add_argument('--name', default='Gustavo_Henrique_de_Jesus_da_Silva', help='Full name for output filename')

    args = parser.parse_args()

    # Resolve paths
    template_path = Path(args.template).resolve()
    base_path = Path(args.base).resolve()
    job_path = Path(args.job).resolve()
    output_dir = Path(args.output_dir).resolve()
    full_name = args.name

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading base curriculum: {base_path}")
    base_data = load_json(base_path)

    print(f"Loading job data: {job_path}")
    job_data = load_json(job_path)

    print("Merging data...")
    merged_data = merge_data(base_data, job_data)

    print(f"Rendering template: {template_path}")
    rendered_tex = render_template(template_path, merged_data)

    # Write temporary .tex file
    temp_tex = output_dir / 'temp_rendered.tex'
    with open(temp_tex, 'w', encoding='utf-8') as f:
        f.write(rendered_tex)

    print("Compiling with xelatex...")
    pdf_path = compile_latex(temp_tex, output_dir, job_data.get('job_slug', 'job'), full_name)

    # Clean up temp files
    for ext in ['.tex', '.aux', '.log', '.out', '.fls', '.fdb_latexmk']:
        temp_file = output_dir / f"curriculo_{full_name.replace(' ', '_')}_{job_data.get('job_slug', 'job')}{ext}"
        if temp_file.exists() and temp_file != pdf_path:
            try:
                temp_file.unlink()
            except:
                pass

    # Clean up main temp file
    if temp_tex.exists():
        temp_tex.unlink()

    print(f"\n✅ PDF generated successfully: {pdf_path}")
    print(f"   Size: {pdf_path.stat().st_size / 1024:.1f} KB")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)