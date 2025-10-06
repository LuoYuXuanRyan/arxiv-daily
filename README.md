Arxiv Daily – Automated arXiv Fetching, LLM‑Based Recommendation & Email Digest
=============================================================================

An automated pipeline that:
1. Fetches the latest papers from arXiv using a configurable query.
2. Filters & categorizes papers via an LLM using your declared research interests.
3. Generates a Markdown summary (and optionally a PDF via Pandoc).
4. Emails the daily recommendations to one or more recipients.
5. Avoids re‑processing papers already handled today (ID cache).

---

## Quick Start

```bash
# 1. Clone this repository
git clone git@github.com:LuoYuXuanRyan/arxiv-daily.git
cd arxiv-daily

# 2. Sync Python virtual environment with uv
uv sync --no-dev

# 3. Install pandoc if you want PDF output
brew install pandoc   # macOS (Homebrew)

# 4. Create a .env file (see sample below) and fill in credentials
cp .env.example .env  # (after you create it or copy from this README)

# 5. Run once
uv run python main.py
```

If everything is configured correctly you should see logs in `./logs/app.log`, a generated Markdown file in `./temp/`, (optionally) a PDF, and an email in your inbox.

---

## Configuration Overview

There are two sources of configuration:

1. `pyproject.toml` – static application configuration under `[tool.arxiv_daily.app]`.
2. `.env` environment variables – secrets & runtime credentials (email + LLM key, etc.).

### 1. pyproject.toml Settings

`[tool.arxiv_daily.app]` block controls query & recommendation behavior.

| Key | Type | Purpose | Example |
|-----|------|---------|---------|
| `timezone` | string | Output/report timezone (for dating files & email subject) | `Asia/Shanghai` |
| `query` | string | arXiv search query (arXiv API syntax) | `cat:cs.LG` |
| `research_interests` | list[str] | High‑level interest tags given to the LLM; used to map & categorize | `["Retrieval-Augmented Generation, RAG", "Agent"]` |
| `max_results` | int | Max papers to fetch per run | `10` |
| `llm_base_url` | string? | Custom API base URL (e.g. DeepSeek / OpenAI proxy). `None` = provider default | `https://api.deepseek.com` |
| `llm_model_name` | string | Chat/completions model name | `deepseek-chat` |

You can change these and re‑run without restarting anything else.

### 2. Environment Variables (.env)

Create a `.env` file in the project root. (The code loads it via `python-dotenv`.)

Required for Email:
- `EMAIL_SENDER` – From address (e.g. notifications@yourdomain.com)
- `EMAIL_RECEIVERS` – Comma separated recipients (e.g. alice@example.com,bob@example.com)
- `SMTP_SERVER` – SMTP host (e.g. smtp.gmail.com)
- `SMTP_PORT` – SMTP port (e.g. 587 for STARTTLS)
- `SMTP_USERNAME` – Username/login (often same as sender email)
- `SMTP_PASSWORD` – SMTP password or app password (read at send time, not stored)

Required for LLM:
- `LLM_API_KEY` – API key for the model provider (DeepSeek, OpenAI, etc.)

Optional:
- You can omit PDF support; if Pandoc is missing the code logs a warning and continues.

Sample `.env`:

```dotenv
EMAIL_SENDER="papers@yourdomain.com"
EMAIL_RECEIVERS="you@yourdomain.com,collab@another.org"
SMTP_SERVER="smtp.yourdomain.com"
SMTP_PORT=587
SMTP_USERNAME="papers@yourdomain.com"
SMTP_PASSWORD="YOUR_SMTP_APP_PASSWORD"

# LLM
LLM_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

Never commit real credentials. Add `.env` to `.gitignore` (it usually is). If not, do so.

> Tip: A ready-to-edit template is provided as `.env.example`. Run:
> ```bash
> cp .env.example .env
> ```
> then fill in real secrets. Keep `.env.example` generic (no real keys) so collaborators know what variables are required.

---

## How It Works (Pipeline Flow)

1. Load settings from `pyproject.toml` & `.env`.
2. Query arXiv (`arxiv` library) with the configured `query` and limit.
3. Convert each result into a `Paper` instance; skip those already in today's cache (`cache/processed_ids.json`).
4. Build a big prompt: research interests + all paper titles/abstracts.
5. Ask the LLM (JSON enforced) to return recommended paper IDs with category + reason.
6. Group papers by category.
7. Generate Markdown report (`temp/new_papers_<date>.md`).
8. Try to convert to PDF via Pandoc (if installed); on failure it logs and continues.
9. Email the Markdown (and PDF if produced) as attachments.
10. Append processed paper IDs to today's cache so reruns the same day skip duplicates.

Cache file shape:
```json
{
	"date": "2025-10-06",
	"ids": ["2501.01234", "2501.05678"]
}
```

---

## File / Module Guide

| File | Purpose |
|------|---------|
| `main.py` | Orchestrates daily flow (fetch → recommend → generate → email → cache). |
| `settings.py` | Loads TOML settings + env vars into dataclasses. |
| `utils.py` | LLM call helper, email sender, timezone conversion, cache helpers. |
| `paper.py` | Simple `Paper` value object. |
| `prompts.py` | System + user prompt templates for the recommender. |
| `construct_pdf.py` | Markdown + (optional) PDF generation using Pandoc. |
| `cache/processed_ids.json` | Daily processed paper ID cache. |
| `logs/app.log` | Rolling append log file. |
| `temp/` | Generated daily Markdown / PDF artifacts. |

---

## Running Manually

```bash
source .venv/bin/activate
uv run python main.py
```

Exit codes:
- `0` normal success or no new papers
- Non‑zero only on uncaught exceptions

Logs: `tail -f logs/app.log` while running.

---

## Scheduling (Automation)

### cron (macOS / Linux)
Run every weekday at 08:00 local time:
```cron
0 8 * * 1-5 cd /absolute/path/to/arxiv-daily && /absolute/path/to/arxiv-daily/.venv/bin/python main.py >> logs/cron.out 2>&1
```

### launchd (macOS alternative)
Create a LaunchAgent plist triggering the same command (optional).

### GitHub Actions (Daily Digest)
If you also want to push generated Markdown back to the repo, create `.github/workflows/daily.yml`:
```yaml
name: Arxiv Daily

on:
    schedule:
        # 00:00 UTC -> 08:00 Asia/Shanghai
        - cron: '0 0 * * *'
    workflow_dispatch: {}

concurrency:
    group: arxiv-daily
    cancel-in-progress: false

env:
    TZ: Asia/Shanghai
    PYTHONUNBUFFERED: '1'

jobs:
    daily:
        name: Fetch & Recommend Papers
        runs-on: ubuntu-latest
        env:
            TZ: Asia/Shanghai
            PYTHONUNBUFFERED: '1'
            LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
            SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
            EMAIL_SENDER: ${{ secrets.EMAIL_SENDER }}
            EMAIL_RECEIVERS: ${{ secrets.EMAIL_RECEIVERS }}
            SMTP_USERNAME: ${{ secrets.SMTP_USERNAME }}
            SMTP_SERVER: ${{ secrets.SMTP_SERVER }}
            SMTP_PORT: ${{ secrets.SMTP_PORT }}
        permissions:
            contents: read
            actions: read
        steps:
            - name: Checkout repository
              uses: actions/checkout@v4
              with:
                  fetch-depth: 0

            - name: Set up Python
              uses: actions/setup-python@v5
              with:
                  python-version: '3.12'

            - name: Install uv (fast Python dependency resolver)
              uses: astral-sh/setup-uv@v3

            - name: Sync dependencies via uv
              run: |
                  uv sync --no-dev

            - name: Install Pandoc & LaTeX (pdflatex)
              run: |
                  sudo apt-get update
                  sudo apt-get install -y pandoc texlive-latex-base texlive-latex-recommended texlive-fonts-recommended
                  pandoc --version

            - name: Prepare runtime folders
              run: |
                  mkdir -p logs temp
                  ls -al

            - name: Run daily script
              run: |
                  echo "Running arxiv daily workflow..."
                  uv run python main.py
                  echo "Execution finished."

            - name: Show log tail
              if: always()
              run: |
                  echo '---- logs/app.log (tail) ----'
                  if [ -f logs/app.log ]; then tail -n 200 logs/app.log; else echo 'No log file.'; fi

            - name: Upload generated markdown
              if: always()
              uses: actions/upload-artifact@v4
              with:
                  name: daily-papers-md
                  path: temp/*.md
                  if-no-files-found: warn

            - name: Upload generated pdf
              uses: actions/upload-artifact@v4
              with:
                  name: daily-papers-pdf
                  path: temp/*.pdf
                  if-no-files-found: warn

            - name: Upload processed id cache
              if: always()
              uses: actions/upload-artifact@v4
              with:
                  name: processed-id-cache
                  path: cache/processed_ids.json
                  if-no-files-found: warn

            - name: Clean up
              if: always()
              run: |
                  echo "Workflow completed."
```

---

## Customizing the LLM Provider

The project uses the `openai` Python client but is model‑agnostic via:
- `llm_base_url` (TOML) – set to a compatible OpenAI‑style endpoint (e.g. DeepSeek, OpenRouter gateway, local proxy).
- `llm_model_name` (TOML) – model ID recognized by that endpoint.
- `LLM_API_KEY` (.env) – secret token.

If your provider does not support the `response_format={type: json_object}` parameter, you will need to adjust `utils.get_llm_json_response` accordingly.

### Improving Recommendation Quality
You can change prompt wording inside `prompts.py` – e.g. tightening novelty criteria or adding disallowed categories. After editing, just rerun.

---

## PDF Generation (Optional)

If Pandoc is installed, a PDF twin of the Markdown report is produced. If not:
- A warning is logged.
- Execution continues and the email still sends the Markdown.

To install Pandoc:
```bash
brew install pandoc          # macOS
sudo apt-get update && sudo apt-get install -y pandoc  # Debian/Ubuntu
```

---

## Error Handling & Logging

| Area | Behavior |
|------|----------|
| LLM JSON parse failure | Logs error, returns empty recommendation set. |
| Pandoc missing/fails | Warning; PDF skipped. |
| SMTP failure | Logs error; script continues (IDs still cached). |
| Cache write failure | Logs error; does not abort main flow. |

View logs:
```bash
tail -f logs/app.log
```

---

## Extending the Project

Ideas:
1. Add HTML email body listing top N papers inline.
2. Add vector store + semantic reranking before prompting the LLM.
3. Retry logic / exponential backoff for LLM & SMTP.
4. Deduplicate categories in LLM response.
5. Add tests (e.g. mock arXiv + mock LLM returning fixture JSON).
6. Add RSS / Slack / Discord notification channel.
7. Add CLI arguments to override `--query` or `--max-results` at runtime.

---

## Minimal Test of LLM Connectivity

From an activated environment (after setting `.env`):
```python
from utils import get_llm_json_response
resp = get_llm_json_response("You are a JSON echo bot.", "Reply with {\"ok\":true}")
print(resp)
```
You should see a JSON string. If you get network / auth errors, verify `LLM_API_KEY`, `llm_base_url`, and model name.

---

## Security Notes

- Never log full API keys or SMTP passwords (the code does not currently, keep it that way).
- Consider rotating keys periodically.
- Use provider‑specific app passwords (e.g. Gmail App Password) instead of your real mailbox password.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Empty recommendations | LLM returned empty / JSON parse failed | Check logs; inspect raw response by adding a temporary print. |
| No email received | SMTP credentials / firewall | Try `telnet smtp.server 587`; enable less secure/app password. |
| PDF not generated | Pandoc missing | Install Pandoc or ignore. |
| Repeated same papers next day | Cache date mismatch/timezone issue | Confirm `timezone` in TOML matches expectation. |
| Slow run | Large `max_results` or slow model | Reduce `max_results`, switch model. |


---

## Attribution

Built with: arXiv API (`arxiv` Python lib), OpenAI‑compatible chat API client, Pandoc.

---

## Changelog

Version 0.1.0 – Initial working pipeline (fetch → recommend → markdown/pdf → email + caching).

---

Happy reading!

