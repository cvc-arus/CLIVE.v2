from fastapi import FastAPI

from simpro_mock.middleware import BearerAuthMiddleware
from simpro_mock.routers import api_router, health_router, token_router

app = FastAPI(title="Simpro Mock API", version="0.1.0")

app.add_middleware(BearerAuthMiddleware)

# Make sure all three routers are registered!
app.include_router(health_router)
app.include_router(token_router)
app.include_router(api_router)
