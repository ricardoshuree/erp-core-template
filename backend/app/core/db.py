# [mcp-local harness] feature: rbac-crud-permission-matrix | plano: 3c4333ee | 2026-08-04 13:42:39
# Seed atualizado para o modelo CRUD de 4 acoes -- editor ganha create/read/update mas nao delete
import uuid

from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import Module, Role, RolePermission, User, UserCreate, UserRole

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# ---------------------------------------------------------------------------
# Roles e módulos padrão do erp-core-template
# Cada ERP filho pode adicionar seus próprios módulos via migration ou seed.
# ---------------------------------------------------------------------------

DEFAULT_ROLES = [
    {"name": "admin",  "description": "Acesso irrestrito a todos os módulos"},
    {"name": "editor", "description": "Cria e edita nos módulos permitidos, mas não apaga"},
    {"name": "viewer", "description": "Somente leitura nos módulos permitidos"},
]

DEFAULT_MODULES = [
    {"name": "usuarios",       "description": "Gestão de usuários e permissões"},
    {"name": "configuracoes",  "description": "Configurações gerais do sistema"},
]


def _get_or_create_role(session: Session, name: str, description: str) -> Role:
    role = session.exec(select(Role).where(Role.name == name)).first()
    if not role:
        role = Role(id=uuid.uuid4(), name=name, description=description)
        session.add(role)
        session.flush()
    return role


def _get_or_create_module(session: Session, name: str, description: str) -> Module:
    module = session.exec(select(Module).where(Module.name == name)).first()
    if not module:
        module = Module(id=uuid.uuid4(), name=name, description=description)
        session.add(module)
        session.flush()
    return module


def _ensure_role_permission(
    session: Session,
    role: Role,
    module: Module,
    can_create: bool,
    can_read: bool,
    can_update: bool,
    can_delete: bool,
) -> None:
    perm = session.exec(
        select(RolePermission)
        .where(RolePermission.role_id == role.id)
        .where(RolePermission.module_id == module.id)
    ).first()
    if not perm:
        perm = RolePermission(
            role_id=role.id,
            module_id=module.id,
            can_create=can_create,
            can_read=can_read,
            can_update=can_update,
            can_delete=can_delete,
        )
        session.add(perm)


def _ensure_user_role(session: Session, user: User, role: Role) -> None:
    exists = session.exec(
        select(UserRole)
        .where(UserRole.user_id == user.id)
        .where(UserRole.role_id == role.id)
    ).first()
    if not exists:
        session.add(UserRole(user_id=user.id, role_id=role.id))


def init_db(session: Session) -> None:
    # ------------------------------------------------------------------
    # 1. Garante que o superuser existe
    # ------------------------------------------------------------------
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)

    # ------------------------------------------------------------------
    # 2. Cria roles e módulos padrão (idempotente — safe pra rodar N vezes)
    # ------------------------------------------------------------------
    roles: dict[str, Role] = {}
    for r in DEFAULT_ROLES:
        roles[r["name"]] = _get_or_create_role(session, r["name"], r["description"])

    modules: dict[str, Module] = {}
    for m in DEFAULT_MODULES:
        modules[m["name"]] = _get_or_create_module(session, m["name"], m["description"])

    # ------------------------------------------------------------------
    # 3. Permissões padrão (CRUD completo por role x módulo):
    #    admin  → create+read+update+delete em todos os módulos base
    #    editor → create+read+update (SEM delete) -- padrão "Gerente"
    #    viewer → somente read em todos os módulos base
    # ------------------------------------------------------------------
    for module in modules.values():
        _ensure_role_permission(
            session, roles["admin"], module,
            can_create=True, can_read=True, can_update=True, can_delete=True,
        )
        _ensure_role_permission(
            session, roles["editor"], module,
            can_create=True, can_read=True, can_update=True, can_delete=False,
        )
        _ensure_role_permission(
            session, roles["viewer"], module,
            can_create=False, can_read=True, can_update=False, can_delete=False,
        )

    # ------------------------------------------------------------------
    # 4. Atribui role admin ao superuser
    # ------------------------------------------------------------------
    _ensure_user_role(session, user, roles["admin"])

    session.commit()
