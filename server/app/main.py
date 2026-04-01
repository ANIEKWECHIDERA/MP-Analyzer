from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .routers.profiles import router as profiles_router
from .routers.reports import router as reports_router

app = FastAPI(title="MP Analyzer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.cors_origins == "*" else [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(profiles_router)
app.include_router(reports_router)
