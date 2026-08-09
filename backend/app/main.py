import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .routers import alerts, applications, companies, jobs, preferences, stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("jobradar")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    if settings.ENABLE_POLLING:
        from .scheduler import start
        start()
    else:
        log.info("polling disabled — set ENABLE_POLLING=true to start the scheduler")
    yield


app = FastAPI(title="Job Radar API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

for r in (jobs, companies, stats, alerts, preferences, applications):
    app.include_router(r.router)


@app.get("/api/health")
def health():
    return {"ok": True, "polling": settings.ENABLE_POLLING}
