# [mcp-local harness] feature: rbac-role-assignment-backend | plano: fde7657e | 2026-08-04 12:36:58
# Registra o novo router de roles
from fastapi import APIRouter

from app.api.routes import items, login, private, roles, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
