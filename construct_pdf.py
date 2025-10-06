from paper import Paper
from datetime import datetime
from utils import to_timezone_time
from pathlib import Path
import logging
import shutil
import subprocess
from settings import load_settings
settings = load_settings(Path("pyproject.toml"))[1]

logger = logging.getLogger(__name__)

def construct_md_file(recommended_papers: dict[str, list[tuple[Paper, str]]]) -> str:
    current_date = datetime.now()
    current_date = to_timezone_time(current_date, settings.timezone).strftime("%Y-%m-%d")
    md_content = f"# New Papers in {current_date} \n\n"
    for category, papers in recommended_papers.items():
        md_content += f"## Category: {category}\n\n"
        for paper, reason in papers:
            authors = ", ".join(paper.authors)
            journal = paper.journal_ref if paper.journal_ref else "N/A"
            md_content += (
                f"### {paper.title}\n"
                f"- **ID**: {paper.ID}\n"
                f"- **Authors**: {authors}\n"
                f"- **Published Date**: {paper.publish_date}\n"
                f"- **Link**: [arXiv Link]({paper.link})\n"
                f"- **Abstract**: {paper.abstract}\n"
                f"- **Journal Reference**: {journal}\n"
                f"- **Reason for Recommendation**: {reason}\n\n"
            )
    output_dir = Path('./temp')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"new_papers_{current_date}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    return str(output_file)

def construct_pdf_file(md_file_path: Path) -> None:
    if not md_file_path.exists() or not md_file_path.is_file():
        raise FileNotFoundError(f"Markdown file not found: {md_file_path}")

    if md_file_path.suffix.lower() != ".md":
        raise ValueError("construct_pdf_file expects a Markdown (.md) file")

    pandoc_path = shutil.which("pandoc")
    if pandoc_path is None:
        raise RuntimeError(
            "Pandoc executable not found. Please install Pandoc and ensure it is on your PATH."
        )

    output_pdf_path = md_file_path.with_suffix(".pdf")
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Converting markdown to PDF using Pandoc: %s -> %s", md_file_path, output_pdf_path)

    process = subprocess.run(
        [pandoc_path, str(md_file_path), "-o", str(output_pdf_path)],
        capture_output=True,
        text=True,
        check=False
    )

    if process.returncode != 0:
        logger.error("Pandoc conversion failed: %s", process.stderr.strip())
        raise RuntimeError(
            "Pandoc failed with exit code "
            f"{process.returncode}: {process.stderr.strip()}"
        )

    logger.info("PDF successfully generated at %s", output_pdf_path)