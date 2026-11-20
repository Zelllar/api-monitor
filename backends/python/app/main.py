from fastapi import FastAPI
from app.routes import router
from contextlib import asynccontextmanager
from app.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()

    yield

    stop_scheduler()

app = FastAPI(
    title="API Monitor",
    description="API monitoring service",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "API Monitor is running"}