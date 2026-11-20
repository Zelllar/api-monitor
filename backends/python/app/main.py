from fastapi import FastAPI, Request, HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.routes import router
from contextlib import asynccontextmanager
from app.scheduler import start_scheduler, stop_scheduler

import logging

logger = logging.getLogger(__name__)

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

@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(
    request: Request,
    exc: FastAPIHTTPException
):
    if exc.status_code == 404:
        code = "MONITOR_NOT_FOUND"
    elif exc.status_code == 422:
        code = "VALIDATION_ERROR"
    else:
        code = "INTERNAL_ERROR"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": str(exc.detail)
            }
        }
    )

@app.exception_handler(StarletteHTTPException)
async def starlette_exception_handler(
    request: Request,
    exc: StarletteHTTPException
):
    if exc.status_code == 404:
        code = "NOT_FOUND"
    else:
        code = "HTTP_ERROR"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": str(exc.detail)
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed"
            }
        }
    )

@app.exception_handler(Exception)
async def internal_exception_handler(
    request: Request,
    exc: Exception
):
    logger.exception("Unexpected server error")

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error"
            }
        }
    )

app.include_router(router)


@app.get("/")
def root():
    return {"message": "API Monitor is running"}