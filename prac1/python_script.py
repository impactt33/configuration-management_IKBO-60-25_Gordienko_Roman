# yaica

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka.integrations.faststream import setup_dishka
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.di import create_container
from src.exceptions import register_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="MIREA MEDIA APP",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        openapi_url="/openapi.json" if settings.SHOW_DOCS else None
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    register_exception_handler(app)

    container = create_container()
    setup_dishka(container=container, app=app)

    return app
