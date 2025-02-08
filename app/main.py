import os
import re
import html
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from datetime import datetime
from supabase import create_client, Client
import markdown
from dotenv import load_dotenv

load_dotenv()

# Load Supabase Credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")
templates.env.filters["markdown"] = lambda text: markdown.markdown(text or "", extensions=["extra", "nl2br"])

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def index(request: Request, date: str = None):
    if (date is None):
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Fetch today's papers immediately
    response = (
        supabase.table("daily_paper_summary")
        .select("id, title, major_topics")
        .filter("upload_date", "eq", date)
        .execute()
    )
    papers = response.data if response.data else []

    return templates.TemplateResponse("index.html", {"request": request, "selected_date": date, "papers": papers})

@app.get("/papers")
async def get_papers(request: Request, date: str):
    """Fetches papers for the selected date from Supabase"""
    response = supabase.table("daily_paper_summary").select("id, title, major_topics").filter("upload_date", "eq", date).execute()
    
    if response.data:
        papers = response.data
    else:
        papers = []

    return templates.TemplateResponse("paper_list.html", {"request": request, "papers": papers})

def clean_markdown(text):
    if not text:
        return ""

    # Normalize heading syntax by removing leading spaces before "#"
    text = re.sub(r"^\s+(#)", r"\1", text, flags=re.MULTILINE)

    return markdown.markdown(html.escape(text))

@app.get("/paper/{paper_id}")
async def get_paper_detail(request: Request, paper_id: int, tab: str = "summary"):
    """Fetches paper details and serves tabbed content dynamically if requested via HTMX."""
    
    response = supabase.table("daily_paper_summary").select("id, title, summary, translate, minor_topics, link, paper_types").eq("id", paper_id).execute()
    
    if response.data and len(response.data) > 0:
        paper = response.data[0]
        paper["summary"] = clean_markdown(paper.get("summary") or "")
        paper["translate"] = clean_markdown(paper.get("translate") or "")
    else:
        return HTMLResponse("<p>Paper not found.</p>", status_code=404)

    # Otherwise, return the full template
    return templates.TemplateResponse("paper_detail.html", {"request": request, "paper": paper, "tab": tab})
