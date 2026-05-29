from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
from .database import engine, Base
from .routers import auth_router, memorial_router, shukatsu_router
from .models import activity_log  # noqa: F401 — ensure ActivityLog table is created
from .config import settings
from .scheduler import start_scheduler, stop_scheduler

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Digital Memorial API", version="0.1.0", lifespan=lifespan)

cors_origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router, prefix="/api")
app.include_router(memorial_router, prefix="/api")
app.include_router(shukatsu_router, prefix="/api")


@app.get("/")
def root():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "Digital Memorial API"}


# React SPA のキャッチオール（Docker ビルド時のみ有効）
if os.path.exists("static"):
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = f"static/{full_path}"
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse("static/index.html")
