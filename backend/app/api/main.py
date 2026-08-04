# [mcp-local harness] feature: rbac-permission-matrix-and-produtos | plano: 5220fc65 | 2026-08-04 14:13:20
# Registra o router de modules
from fastapi import APIRouter

from app.api.routes import items, login, modules, private, roles, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(modules.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
