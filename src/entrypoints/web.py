import asyncio
import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.channels.web.adapter import router as web_router
from src.core.logging import uvicorn_log_config
from src.llm.client import LLMClient
from src.storage.database import init_db

logger = logging.getLogger(__name__)


def _build_web_app(config):
    app = FastAPI(title="DentalFlow AI Web Channel")

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "dentalflow"}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(web_router)
    app.state.config = config
    app.state.llm_client = LLMClient(
        api_key=config.openai_api_key,
        model=config.openai_model,
    )
    return app


def run_web(config) -> None:
    asyncio.run(init_db())
    app = _build_web_app(config)
    logger.info("Starting web channel on http://%s:%s", config.web_host, config.web_port)
    uvicorn.run(
        app,
        host=config.web_host,
        port=config.web_port,
        log_level=config.log_level.lower(),
        log_config=uvicorn_log_config(config.log_level, os.getenv("LOG_FORMAT", "json")),
    )


if __name__ == "__main__":
    from src.bootstrap import bootstrap

    cfg = bootstrap()["config"]
    run_web(cfg)