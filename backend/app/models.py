# [mcp-local harness] feature: fix-models-comment-leak | plano: b966d0fc | 2026-08-04 15:00:30
# Remove referencia ao gasfavero/produtos.tsx do comentario, volta ao texto generico
import uuid
from datetime import UTC, datetime

from pydantic import EmailStr
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# RBAC — Role
# ---------------------------------------------------------------------------

class Role(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, max_length=100)
    description: str | None = Field(default=None, max_length=255)

    user_roles: list["UserRole"] = Relationship(back_populates="role")
    permissions: list["RolePermission"] = Relationship(back_populates="role")


# ---------------------------------------------------------------------------
# RBAC — Module
# ---------------------------------------------------------------------------

class Module(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, max_length=100)
    description: str | None = Field(default=None, max_length=255)

    permissions: list["RolePermission"] = Relationship(back_populates="module")


# ---------------------------------------------------------------------------
# RBAC — RolePermission (matriz role x module x ação)
#
# 4 ações CRUD independentes -- ex: uma role pode criar/editar mas não
# apagar (o exemplo clássico de "Gerente"), o que não era possível
# expressar com o antigo can_read/can_edit único.
# ---------------------------------------------------------------------------

class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permission"

    role_id: uuid.UUID = Field(
        foreign_key="role.id", primary_key=True, ondelete="CASCADE"
    )
    module_id: uuid.UUID = Field(
        foreign_key="module.id", primary_key=True, ondelete="CASCADE"
    )
    can_create: bool = Field(default=False)
    can_read: bool = Field(default=False)
    can_update: bool = Field(default=False)
    can_delete: bool = Field(default=False)

    role: Role = Relationship(back_populates="permissions")
    module: Module = Relationship(back_populates="permissions")


# ---------------------------------------------------------------------------
# RBAC — UserRole (liga User ao Role)
# ---------------------------------------------------------------------------

class UserRole(SQLModel, table=True):
    __tablename__ = "user_role"

    user_id: uuid.UUID = Field(
        foreign_key="user.id", primary_key=True, ondelete="CASCADE"
    )
    role_id: uuid.UUID = Field(
        foreign_key="role.id", primary_key=True, ondelete="CASCADE"
    )

    user: "User" = Relationship(back_populates="roles")
    role: Role = Relationship(back_populates="user_roles")


# ---------------------------------------------------------------------------
# RBAC — Response models (usados pelo endpoint /users/me/permissions)
# ---------------------------------------------------------------------------

class ModulePermission(SQLModel):
    """Permissão efetiva de um usuário em um módulo específico (CRUD)."""
    module: str
    description: str | None = None
    can_create: bool
    can_read: bool
    can_update: bool
    can_delete: bool


class UserPermissions(SQLModel):
    """Resposta completa de permissões do usuário logado."""
    is_superuser: bool
    roles: list[str]
    permissions: list[ModulePermission]


# ---------------------------------------------------------------------------
# RBAC — Response models (usados pela tela de administração de Usuários,
# gestão de roles: listar roles disponíveis e atribuir a um usuário)
# ---------------------------------------------------------------------------

class RolePublic(SQLModel):
    """Role RBAC exposta pra UI (não confundir com is_superuser)."""
    id: uuid.UUID
    name: str
    description: str | None = None


class RolesPublic(SQLModel):
    data: list[RolePublic]


class UserRolesUpdate(SQLModel):
    """Corpo de PUT /users/{user_id}/roles -- substitui o conjunto
    inteiro de roles do usuário pelos ids informados (lista vazia
    remove todas as roles)."""
    role_ids: list[uuid.UUID]


# ---------------------------------------------------------------------------
# RBAC — Response models (tela de administração da matriz de
# permissões: Módulo x Role x Ação CRUD)
# ---------------------------------------------------------------------------

class ModulePublic(SQLModel):
    id: uuid.UUID
    name: str
    description: str | None = None


class ModulesPublic(SQLModel):
    data: list[ModulePublic]


class RolePermissionEntry(SQLModel):
    """Uma linha da matriz: o que uma role específica pode fazer no
    módulo (zerado se ainda não houver RolePermission cadastrado)."""
    role_id: uuid.UUID
    role_name: str
    can_create: bool
    can_read: bool
    can_update: bool
    can_delete: bool


class ModulePermissionMatrix(SQLModel):
    module: ModulePublic
    entries: list[RolePermissionEntry]


class RolePermissionUpdate(SQLModel):
    role_id: uuid.UUID
    can_create: bool = False
    can_read: bool = False
    can_update: bool = False
    can_delete: bool = False


class ModulePermissionMatrixUpdate(SQLModel):
    """Corpo de PUT /modules/{module_id}/permissions -- grava a
    matriz inteira do módulo de uma vez (upsert por role)."""
    entries: list[RolePermissionUpdate]


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    roles: list["UserRole"] = Relationship(back_populates="user", cascade_delete=True)


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class UserPublicWithRoles(UserPublic):
    """UserPublic + nomes das roles RBAC atribuídas -- usado pela
    tabela de Usuários na tela de admin, que mostra e permite editar
    as roles de cada um."""
    roles: list[str] = []


class UsersPublicWithRoles(SQLModel):
    data: list[UserPublicWithRoles]
    count: int


# ---------------------------------------------------------------------------
# Item (mantido do template original)
# ---------------------------------------------------------------------------

class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# ---------------------------------------------------------------------------
# Auth / Token
# ---------------------------------------------------------------------------

class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
