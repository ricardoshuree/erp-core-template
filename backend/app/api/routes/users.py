# [mcp-local harness] feature: fix-project-name-leak | plano: 7563fe1b | 2026-08-04 11:51:04
# Troca 'gasfavero' por termo generico 'este template' no comentario
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import col, delete, func, select

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (
    Item,
    Message,
    Module,
    ModulePermission,
    RolePermission,
    UpdatePassword,
    User,
    UserCreate,
    UserPermissions,
    UserPublic,
    UserRegister,
    UserRole,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """Retrieve users."""
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()
    statement = (
        select(User).order_by(col(User.created_at).desc()).offset(skip).limit(limit)
    )
    users = session.exec(statement).all()
    users_public = [UserPublic.model_validate(user) for user in users]
    return UsersPublic(data=users_public, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """Create new user."""
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """Get current user."""
    return current_user


@router.get("/me/permissions", response_model=UserPermissions)
def read_user_permissions(
    current_user: CurrentUser, session: SessionDep
) -> UserPermissions:
    """
    Retorna os módulos e permissões efetivas do usuário logado.

    Superusuários recebem can_read=True e can_edit=True em todos os módulos
    cadastrados, independente de roles atribuídos.

    Usado pelo frontend para renderizar o menu lateral dinamicamente.
    """
    # Busca todos os roles do usuário
    user_roles = session.exec(
        select(UserRole).where(UserRole.user_id == current_user.id)
    ).all()
    role_names = []
    role_ids = []
    for ur in user_roles:
        role_ids.append(ur.role_id)
        if ur.role:
            role_names.append(ur.role.name)

    # Busca todos os módulos cadastrados
    all_modules = session.exec(select(Module)).all()

    permissions: list[ModulePermission] = []

    if current_user.is_superuser:
        # Superuser tem acesso total a todos os módulos
        for module in all_modules:
            permissions.append(
                ModulePermission(
                    module=module.name,
                    description=module.description,
                    can_read=True,
                    can_edit=True,
                )
            )
    else:
        # Agrega permissões de todos os roles do usuário por módulo
        for module in all_modules:
            if not role_ids:
                continue
            perms = session.exec(
                select(RolePermission)
                .where(RolePermission.role_id.in_(role_ids))
                .where(RolePermission.module_id == module.id)
            ).all()
            if not perms:
                continue
            # OR entre os roles: se qualquer role permite, o usuário pode
            can_read = any(p.can_read for p in perms)
            can_edit = any(p.can_edit for p in perms)
            if can_read or can_edit:
                permissions.append(
                    ModulePermission(
                        module=module.name,
                        description=module.description,
                        can_read=can_read,
                        can_edit=can_edit,
                    )
                )

    return UserPermissions(
        is_superuser=current_user.is_superuser,
        roles=role_names,
        permissions=permissions,
    )


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """Update own user."""
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """Update own password."""
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """Delete own user."""
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


# ---------------------------------------------------------------------------
# Auto-cadastro público (B2C) -- DESABILITADO
#
# Reservado para uma futura abertura do canal de vendas B2C (cliente
# final / comprador varejista se cadastrando sozinho). Por padrão este
# template é um sistema fechado: só um admin cria contas (ver POST
# /users/ acima, protegido por superuser).
#
# Lógica original preservada em comentário para reativação futura --
# ao religar, restaurar o corpo da função e remover o HTTPException 403:
#
#     user = crud.get_user_by_email(session=session, email=user_in.email)
#     if user:
#         raise HTTPException(
#             status_code=400,
#             detail="The user with this email already exists in the system",
#         )
#     user_create = UserCreate.model_validate(user_in)
#     user = crud.create_user(session=session, user_create=user_create)
#     return user
# ---------------------------------------------------------------------------
@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """Auto-cadastro público -- desabilitado, ver comentário acima."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Cadastro público desabilitado. Peça a um administrador "
            "para criar sua conta."
        ),
    )


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get a specific user by id."""
    user = session.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """Update a user."""
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """Delete a user."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    statement = delete(Item).where(col(Item.owner_id) == user_id)
    session.exec(statement)
    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")
