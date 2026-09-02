import secrets
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from scalar_fastapi import get_scalar_api_reference
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

from src.api.v1.router import api_router
from src.config import settings
from src.core.logging import setup_logging
from src.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)

# Import all models so SQLAlchemy registers every table before any query.
from src.food.models import (  # noqa: F401
    CategoryProduct,
    Menu,
    MenuAvailability,
    ModifierGroup,
    ModifierGroupOption,
    Product,
    ProductModifierGroup,
    ProductPrice,
)
from src.category.models import MenuCategory  # noqa: F401
from src.schemas import HealthResponse
from src.stores.models import Store  # noqa: F401

if settings.sentry_dsn and settings.environment != "local":
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        send_default_pii=False,
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if not settings.debug:
            response.headers["Content-Security-Policy"] = "default-src 'none'"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    yield


docs_enabled = settings.environment in ("local", "development")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    # Disable the built-in /openapi.json route so we can serve it ourselves
    # behind HTTP Basic when docs are enabled.
    openapi_url=None,
)

# Security headers middleware (added before CORS so headers are always set)
app.add_middleware(SecurityHeadersMiddleware)

# Response compression for the (potentially large) all-menus payload.
app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API routers
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", response_model=HealthResponse, tags=["Health"], include_in_schema=False)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy", version=settings.app_version)


@app.get("/", tags=["Root"], include_in_schema=False)
async def root() -> dict[str, str]:
    return {"message": f"Welcome to {settings.app_name}"}


if docs_enabled:
    """Scalar API documentation and OpenAPI schema: HTTP Basic protected."""

    _docs_security = HTTPBasic()
    _OPENAPI_PATH = "/openapi.json"

    def _verify_docs_credentials(
        credentials: HTTPBasicCredentials = Depends(_docs_security),
    ) -> None:
        expected_user = settings.docs_basic_auth_username
        expected_pass = settings.docs_basic_auth_password
        if not expected_user or not expected_pass:
            # Credentials not configured — fail closed in dev/local rather than
            # silently exposing the docs.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Docs basic auth credentials not configured",
            )
        user_ok = secrets.compare_digest(credentials.username, expected_user)
        pass_ok = secrets.compare_digest(credentials.password, expected_pass)
        if not (user_ok and pass_ok):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )

    @app.get("/docs", include_in_schema=False)
    async def scalar_html(_: None = Depends(_verify_docs_credentials)):
        return get_scalar_api_reference(
            openapi_url=_OPENAPI_PATH,
            hide_models=True,
        )

    @app.get("/menu", include_in_schema=False)
    async def swagger_html(_: None = Depends(_verify_docs_credentials)):
        return get_swagger_ui_html(openapi_url=_OPENAPI_PATH, title=f"{settings.app_name} - Swagger")

    @app.get(_OPENAPI_PATH, include_in_schema=False)
    async def openapi_schema(_: None = Depends(_verify_docs_credentials)):
        return app.openapi()
