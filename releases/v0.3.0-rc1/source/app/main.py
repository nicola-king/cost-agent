from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.db import Base, engine
from app.api.routes import router
from app import plugins  # register capabilities
from app.services.identity_middleware import IdentityBindingMiddleware

BASE = Path(__file__).resolve().parent
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Construction Cost Intelligence", version="0.3.0-rc1")
app.add_middleware(IdentityBindingMiddleware)
app.include_router(router)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/mobile", response_class=HTMLResponse)
def mobile(request: Request):
    return templates.TemplateResponse(request, "mobile.html")
