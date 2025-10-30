from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from .db import db_pool
from .routers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_pool.connect()
    yield
    await db_pool.close()


app = FastAPI(default_response_class=ORJSONResponse, lifespan=lifespan, title="SWL Remote DB")

app.include_router(router, prefix="/v1")


