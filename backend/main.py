from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.routes import decisions, portfolio, queue, sku
from db.init import initialize_database
from services.signal_engine import load_data_stores


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await initialize_database()
    load_data_stores()
    yield


app = FastAPI(lifespan=lifespan, title="Opptra Pricing Intelligence API")

# ADD THIS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    portfolio.router,
    prefix="/api/portfolio",
    tags=["portfolio"],
)
app.include_router(queue.router, prefix="/api/queue", tags=["queue"])
app.include_router(sku.router, prefix="/api/sku", tags=["sku"])
app.include_router(
    decisions.router,
    prefix="/api/decisions",
    tags=["decisions"],
)

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
