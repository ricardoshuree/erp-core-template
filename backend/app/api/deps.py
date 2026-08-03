# [mcp-local harness] feature: rbac-tests | plano: f82f1589 | 2026-08-03 14:49:41
# Converte sub do JWT para uuid.UUID antes do session.get — corrige StatementError no SQLite
import uuid
from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session, select

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import Module, RolePermission, TokenPayload, User, UserRole

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    # Converte sub (string) para UUID — necessário para compatibilidade com
    # SQLite (testes) e Postgres (produção), já que session.get espera UUID.
    try:
        user_id = uuid.UUID(token_data.sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


# ---------------------------------------------------------------------------
# RBAC — guard de permissão por módulo
# ---------------------------------------------------------------------------

def require_module_permission(module_name: str, need_edit: bool = False):
    """
    Factory de Depends para proteger rotas por módulo e nível de acesso.

    Uso:
        CanReadClientes  = Depends(require_module_permission("clientes"))
        CanEditClientes  = Depends(require_module_permission("clientes", need_edit=True))

        @router.get("/clientes", dependencies=[CanReadClientes])
        def list_clientes(): ...

        @router.post("/clientes", dependencies=[CanEditClientes])
        def create_cliente(): ...

    Superusuários passam direto — têm acesso irrestrito a todos os módulos.
    """
    def checker(current_user: CurrentUser, session: SessionDep) -> User:
        if current_user.is_superuser:
            return current_user

        user_roles = session.exec(
            select(UserRole).where(UserRole.user_id == current_user.id)
        ).all()
        role_ids = [ur.role_id for ur in user_roles]

        if not role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem roles atribuídos a este usuário",
            )

        module = session.exec(
            select(Module).where(Module.name == module_name)
        ).first()
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Módulo '{module_name}' não encontrado",
            )

        stmt = (
            select(RolePermission)
            .where(RolePermission.role_id.in_(role_ids))
            .where(RolePermission.module_id == module.id)
        )
        if need_edit:
            stmt = stmt.where(RolePermission.can_edit == True)  # noqa: E712
        else:
            stmt = stmt.where(RolePermission.can_read == True)  # noqa: E712

        perm = session.exec(stmt).first()

        if not perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Sem permissão de {'edição' if need_edit else 'leitura'} no módulo '{module_name}'",
            )

        return current_user

    return checker
