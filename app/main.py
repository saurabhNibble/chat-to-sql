import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.api.v1.endpoints.health import check_health
from app.api.v1.endpoints.query import handle_query
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import logger
from app.core.security import check_rate_limit
from app.db.connection import close_db_pool, init_db_pool
from app.models.query import HealthResponse, QueryResponse
from app.ui.chat import get_chat_html_response

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize connection pool
    logger.info("Starting up application lifecycle...")
    try:
        init_db_pool()
    except Exception as exc:
        logger.error(f"Failed to initialize database pool on startup: {exc}")
    yield
    # Shutdown: Close connection pool gracefully
    logger.info("Shutting down application lifecycle...")
    close_db_pool()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate Limiting & Latency Middleware
    @app.middleware("http")
    async def request_processing_middleware(request: Request, call_next):
        # Apply rate limiting to API routes
        if request.url.path.startswith(settings.API_V1_STR) or request.url.path == "/query":
            try:
                check_rate_limit(request)
            except Exception as exc:
                if isinstance(exc, JSONResponse):
                    return exc
                raise

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time * 1000:.2f}ms"
        return response

    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception during {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred. Please contact the administrator.",
                "error_code": "INTERNAL_SERVER_ERROR",
            },
        )

    # Interactive Chat Interface
    @app.get("/chat", response_class=HTMLResponse, include_in_schema=False)
    def chat_ui():
        return get_chat_html_response()

    # Root redirect to Web Chat UI
    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/chat")

    # API v1 routes
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    # Backward-compatible direct aliases for /health and /query
    app.add_api_route(
        "/health",
        check_health,
        methods=["GET"],
        response_model=HealthResponse,
        tags=["Health"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/query",
        handle_query,
        methods=["POST"],
        response_model=QueryResponse,
        tags=["Text-to-SQL Query"],
        include_in_schema=False,
    )

    return app


app = create_app()
