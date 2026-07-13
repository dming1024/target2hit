"""FastAPI application factory."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import pipeline, screening, docking, jobs

app = FastAPI(
    title="Target2Hit Discovery Platform",
    version="0.1.0",
    description="AI-driven Target-to-Hit Discovery Pipeline",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline"])
app.include_router(screening.router, prefix="/api/v1/screening", tags=["Screening"])
app.include_router(docking.router, prefix="/api/v1/docking", tags=["Docking"])
app.include_router(jobs.router, prefix="/api/v1/job", tags=["Jobs"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
