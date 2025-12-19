"""ASGI application entrypoint."""

from collections.abc import Awaitable, Callable
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.app.api.health import router as health_router
from src.app.api.routes.quotations import router as quotations_router
from src.app.api.routes.chat import router as chat_router
from src.app.api.routes.quotes import router as quotes_router
from src.app.config import settings
from src.app.data_models.common import ErrorResponse, StatusEnum

RequestHandler = Callable[[Request], Awaitable[Response]]


def _detect_app_version() -> str:
    """Return installed package version or fallback for local development."""
    try:
        return version("bakery-quotation-agent")
    except PackageNotFoundError:
        return "0.1.0"


APP_VERSION = _detect_app_version()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    app = FastAPI(
        title=settings.app_name,
        description="AI-powered bakery quotation system with LangChain agent orchestration",
        version=APP_VERSION,
        docs_url=settings.docs_url,
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    register_event_handlers(app)
    register_routes(app)
    register_default_routes(app)

    return app


def register_routes(app: FastAPI) -> None:
    """Attach API routers to the application."""

    app.include_router(health_router)
    app.include_router(quotations_router, prefix=settings.api_prefix)
    app.include_router(chat_router, prefix=settings.api_prefix)
    app.include_router(quotes_router, prefix=settings.api_prefix)


def register_default_routes(app: FastAPI) -> None:
    """Include default root endpoint."""

    @app.get("/", tags=["info"])
    async def root() -> dict[str, Any]:
        return {
            "message": settings.app_name,
            "version": APP_VERSION,
            "status": "active",
            "documentation": settings.docs_url,
            "timestamp": datetime.now().isoformat(),
        }


def register_event_handlers(app: FastAPI) -> None:
    """Attach lifecycle handlers."""

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Don't handle HTTPExceptions - let FastAPI handle them naturally
        if isinstance(exc, HTTPException):
            raise exc

        logger.error(f"Unhandled exception: {exc!s}")

        error_response = ErrorResponse(
            status=StatusEnum.FAILURE,
            error_code="INTERNAL_ERROR",
            error_message="An unexpected error occurred",
            details={"error": str(exc)},
        )

        return JSONResponse(status_code=500, content=jsonable_encoder(error_response))

    @app.middleware("http")
    async def log_requests(request: Request, call_next: RequestHandler) -> Response:
        """Log request lifecycle information and add diagnostic headers."""

        start_time = datetime.now()
        logger.info(f"Request: {request.method} {request.url.path}")

        response = await call_next(request)

        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Response: {response.status_code} - Processing time: {process_time:.3f}s"
        )

        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-API-Version"] = APP_VERSION

        return response


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)  # noqa: S104
