# [mcp-local harness] feature: supabase-auth-backend | plano: 82afe850 | 2026-08-04 00:41:47
# get_current_user com fallback aditivo para tokens do Supabase Auth, auto-provisionamento de usuario sem roles
# [mcp-local harness] feature: rbac-tests | plano: f82f1589 | 2026-08-03 14:49:41
# Converte sub do JWT para uuid.UUID antes do session.get — corrige StatementError no SQLite
#
# [mcp-local harness] feature: supabase-auth-backend | plano: 82afe850 | 2026-08-04 00:41
# get_current_user agora tenta o JWT local primeiro (compatibilidade com
# o FIRST_SUPERUSER seedado e qualquer login por senha existente) e, se
# falhar, tenta verificar como um JWT do Supabase Auth (login Google).
# Na primeira vez que um usuário autenticado via Supabase aparece, um
# User local é criado por email, sem nenhuma role atribuída -- um admin
# precisa atribuir role manualmente antes do usuário ter qualquer
# permissão além do próprio perfil. NÃO TESTADO ponta a ponta ainda
# (ver aviso em app/core/supabase_auth.py) -- revisar antes de confiar
# em produção.
import secrets
import uuid
from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError, PyJWTError
from pydantic import ValidationError
from sqlmodel import Session, select

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.core.supabase_auth import verify_supabase_token
from app.models import Module, RolePermission, TokenPayload, User, UserRole

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def _get_or_create_user_from_supabase(session: Session, payload: dict) -> User:
    """
    Busca (ou cria) o User local correspondente a um token do Supabase
    Auth, casando por e-mail. Usuários novos entram SEM roles -- um
    admin precisa atribuir manualmente antes de terem qualquer
    permissão além do próprio perfil (/users/me).
    """
    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token do Supabase sem claim de email",
        )

    user = session.exec(select(User).where(User.email == email)).first()
    if user:
        return user

    # Placeholder de senha inutilizável -- este usuário só autentica via
    # Supabase (Google), nunca via /login/access-token local.
    placeholder_password = security.get_password_hash(secrets.token_urlsafe(32))
    user = User(
        email=email,
        full_name=payload.get("user_metadata", {}).get("full_name"),
        hashed_password=placeholder_password,
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    # 1. Tenta como JWT local (fluxo original, email+senha via backend)
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        user_id = uuid.UUID(token_data.sub)
        user = session.get(User, user_id)
        if user:
            if not user.is_active:
                raise HTTPException(status_code=400, detail="Inactive user")
            return user
    except (InvalidTokenError, ValidationError, TypeError, ValueError):
        pass  # não é um JWT local válido -- tenta Supabase abaixo

    # 2. Tenta como JWT do Supabase Auth (login Google, etc.)
    try:
        supabase_payload = verify_supabase_token(token)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    user = _get_or_create_user_from_supabase(session, supabase_payload)
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
