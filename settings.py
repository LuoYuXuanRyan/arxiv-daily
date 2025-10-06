from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
from pathlib import Path
import os
import tomllib
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
load_dotenv()


@dataclass(frozen=True)
class ProjectMeta:
    name: str
    version: str
    description: str


@dataclass(frozen=True)
class AppConfig:
    timezone: str
    query: str
    research_interests: list[str]
    max_results: int
    llm_model_name: str
    email_sender: str
    email_receivers: str
    smtp_server: str
    smtp_port: int
    smtp_username: str
    llm_base_url: Optional[str] = None
    
    @property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

def load_settings(pyproject_path: Path) -> tuple[ProjectMeta, AppConfig]:
    path = pyproject_path
    with open(path, "rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    proj = data.get("project", {})
    meta = ProjectMeta(
        name=proj.get("name", ""),
        version=proj.get("version", ""),
        description=proj.get("description", ""),
    )

    tool = data.get("tool", {})
    app_tbl = tool.get("arxiv_daily", {}).get("app", {}) or {}
    tz = app_tbl.get("timezone", "UTC")
    query = app_tbl.get("query", "cat:cs.LG")
    research_interests = app_tbl.get("research_interests", ["artificial intelligence"])
    max_results = int(app_tbl.get("max_results", 50))
    llm_model_name = app_tbl.get("llm_model_name", "gpt-5-mini")
    llm_base_url = app_tbl.get("llm_base_url", None)
    email_sender = os.getenv("EMAIL_SENDER", "")
    email_receivers = os.getenv("EMAIL_RECEIVERS", "")
    smtp_server = os.getenv("SMTP_SERVER", "")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_username = os.getenv("SMTP_USERNAME", "")
    app_cfg = AppConfig(
        timezone=tz,
        query=query,
        research_interests=research_interests,
        max_results=max_results,
        llm_model_name=llm_model_name,
        llm_base_url=llm_base_url,
        email_sender=email_sender,
        email_receivers=email_receivers,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
    )
    return meta, app_cfg
