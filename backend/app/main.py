from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router
from app.core.config import API_PREFIX, APP_NAME, FRONTEND_DIR
from app.services.repository import FileRepository

app = FastAPI(title=APP_NAME)
FileRepository()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=API_PREFIX)
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
app.mount("/src", StaticFiles(directory=FRONTEND_DIR / "src"), name="src")


@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME}


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")
