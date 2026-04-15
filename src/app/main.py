# The logger is imported and configured first to prevent other imports overridding it
import logging
from opentelemetry.instrumentation.logging import LoggingInstrumentor

LoggingInstrumentor().instrument()
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.db import sessionmanager, add_first_superuser
from app.api.main import api_router
from app.core.config import settings

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.extension.aws.trace import AwsXRayIdGenerator
from opentelemetry.propagators.aws import AwsXRayPropagator
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.propagate import set_global_textmap
from app.utils.log_requests import log_requests

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


def otel_trace_init():
    # The exporter endpoint points to a local adot container.
    # The name is set in the service cluster CDK stack
    try:
        if settings.ENVIRONMENT == "local":
            otlp_exporter = ConsoleSpanExporter()
        else:
            otlp_exporter = OTLPSpanExporter(endpoint="http://collector:4317")
        set_global_textmap(AwsXRayPropagator())
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.set_tracer_provider(
            TracerProvider(
                active_span_processor=span_processor,
                id_generator=AwsXRayIdGenerator(),
            )
        )
    except Exception as e:
        print(f"Unable to initialise otel trace provider. Error: {e}")


otel_trace_init()


def init_app() -> FastAPI:
    """
    Initialize and configure the FastAPI application.

    This function:
    - Sets up the FastAPI server with proper configuration
    - Configures CORS middleware if enabled
    - Includes API routes with proper prefixing
    - Sets up database connection lifecycle management

    Returns:
        FastAPI: The configured FastAPI application instance.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # noqa
        """
        Manage the lifecycle of the FastAPI application.

        This async context manager:
        - Initializes database connection on startup
        - Closes database connections on shutdown
        - Provides proper cleanup of resources

        Args:
            app (FastAPI): The FastAPI application instance.

        Yields:
            None: Control returns to FastAPI during application runtime.
        """
        # Initialize database connection
        url = settings.SQLALCHEMY_DATABASE_URI.unicode_string()
        sessionmanager.init(url)

        async with sessionmanager.session() as session:
            await add_first_superuser(session)
        yield

        # Cleanup database connections
        if sessionmanager._engine is not None:
            await sessionmanager.close()

    # Initialize FastAPI with custom configuration
    server = FastAPI(
        title=settings.PROJECT_NAME,
        lifespan=lifespan,
        generate_unique_id_function=custom_generate_unique_id,
    )

    # Set all CORS enabled origins
    if settings.all_cors_origins:
        server.add_middleware(
            CORSMiddleware,
            allow_origins=settings.all_cors_origins,
            allow_credentials=True,
            allow_methods=["*"],  # Allow all HTTP methods
            allow_headers=["*"],  # Allow all headers
        )

    # Include API routes with version prefix
    server.include_router(api_router, prefix=settings.API_V1_STR)
    FastAPIInstrumentor.instrument_app(
        server, excluded_urls=f"{settings.API_V1_STR}/utils/health-check/"
    )
    return server


# Create the FastAPI application instance
app = init_app()
app.middleware("http")(log_requests)
logging.getLogger("uvicorn.access")