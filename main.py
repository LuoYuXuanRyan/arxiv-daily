import logging
import arxiv
import os
from utils import to_timezone_time, get_llm_json_response, send_email, load_processed_ids, append_processed_ids
from paper import Paper
from prompts import recommender_system_prompt, recommender_user_prompt
import json
from pathlib import Path
from construct_pdf import construct_md_file, construct_pdf_file

from settings import load_settings
settings = load_settings(Path("pyproject.toml"))[1]
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="./logs/app.log",
    filemode="a",
)


def get_arxiv_papers() -> list[Paper]:
    processed_ids = load_processed_ids()
    papers = []
    client = arxiv.Client()
    search = arxiv.Search(
        query=settings.query,
        max_results=settings.max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    for result in client.results(search):
        publish_date = result.published
        publish_date_bj = to_timezone_time(publish_date, settings.timezone)
        paper = Paper(
            ID=result.entry_id.split('/')[-1],
            title=result.title,
            authors=[author.name for author in result.authors],
            publish_date=publish_date_bj,
            link=result.entry_id,
            abstract=result.summary,
            journal_ref=result.journal_ref
        )
        if paper.ID in processed_ids:
            logging.info(f"Skip already processed paper: {paper.ID}")
            continue
        papers.append(paper)
    return papers


def get_recommend_papers(papers: list[Paper]) -> dict[str, list[tuple[Paper, str]]]:
    recommend_papers = {}
    user_research_interests = ", ".join(settings.research_interests)
    paper_info = ""
    for paper in papers:
        title = paper.title
        abstract = paper.abstract
        paper_id = paper.ID
        paper_info += f"""
Paper ID: {paper_id}
Title: {title}
Abstract: {abstract}
"""

    logging.info("Generating recommendations using LLM.")
    response = get_llm_json_response(
        system_prompt=recommender_system_prompt,
        user_prompt=recommender_user_prompt.format(
            user_interests=user_research_interests,
            paper_info=paper_info
        )
    )
    logging.info(f"Received response from LLM: {response}")
    if response:
        try:
            recommend_obj = json.loads(response)
            for item in recommend_obj:
                paper_id = item.get("paper_id", "")
                category = item.get("category", "").lower()
                reason = item.get("reason", "")
                for paper in papers:
                    if paper.ID == paper_id:
                        if category in recommend_papers:
                            recommend_papers[category].append((paper, reason))
                        else:
                            recommend_papers[category] = [(paper, reason)]
                        break
        except json.JSONDecodeError:
            logging.error("Failed to decode answer from LLM response.")
    return recommend_papers


if __name__ == "__main__":
    logging.info("Starting arXiv Daily Paper Recommendation Process")
    all_papers = get_arxiv_papers()
    logging.info(f"Fetched {len(all_papers)} papers from arXiv.")
    if not all_papers:
        logging.info("All latest papers have been processed before. Skip and exit.")
        exit(0)
    recommended_papers = get_recommend_papers(all_papers)
    logging.info(
        f"Recommended {len(recommended_papers)} papers based on research interests.")
    logging.info("Process completed.")
    if not recommended_papers:
        logging.info("No new recommended papers (all filtered or none matched).")
    md_file_path = construct_md_file(recommended_papers=recommended_papers)
    try:
        construct_pdf_file(md_file_path=Path(md_file_path))
    except Exception as e:
        logging.warning(f"PDF generation failed: {e}")
    send_email(attachment_paths=[Path(md_file_path)])
    all_ids = [p.ID for p in all_papers]
    if all_ids:
        append_processed_ids(all_ids)
