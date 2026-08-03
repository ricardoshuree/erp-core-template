# [mcp-local harness] feature: rbac-tests | plano: f4289c06 | 2026-08-03 14:02:24
# Fixtures de usuários por role para testes de RBAC
"""
conftest.py — Fixtures de RBAC para os testes de guards de permissão.

Cada fixture:
  1. Cria um usuário aleatório via crud
  2. Busca o role correspondente (já criado pelo init_db/seed)
  3. Atribui o role ao usuário (UserRole)
  4. Retorna os headers de autenticação Bearer prontos para uso
  5. Remove o usuário no teardown (cascade apaga UserRole automaticamente)

A fixture `no_role_headers` cria um usuário sem nenhum role atribuído,
para testar o bloqueio de acesso quando roles estão ausentes.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.models import Role, User, UserCreate, UserRole
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _create_user_with_role(
    client: TestClient,
    db: Session,
    role_name: str | None,
) -> dict[str, str]:
    """Cria usuário aleatório, opcionalmente atribui um role, retorna headers."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user: User = crud.create_user(session=db, user_create=user_in)

    if role_name is not None:
        role = db.exec(select(Role).where(Role.name == role_name)).first()
        assert role is not None, (
            f"Role '{role_name}' não encontrado — verifique se o init_db rodou corretamente"
        )
        db.add(UserRole(user_id=user.id, role_id=role.id))
        db.commit()

    headers = user_authentication_headers(client=client, email=email, password=password)
    return headers


# ---------------------------------------------------------------------------
# Fixtures públicas
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_headers(client: TestClient, db: Session) -> dict[str, str]:
    """Usuário com role 'admin' — leitura e edição em todos os módulos."""
    return _create_user_with_role(client, db, "admin")


@pytest.fixture
def editor_headers(client: TestClient, db: Session) -> dict[str, str]:
    """Usuário com role 'editor' — leitura e edição nos módulos permitidos."""
    return _create_user_with_role(client, db, "editor")


@pytest.fixture
def viewer_headers(client: TestClient, db: Session) -> dict[str, str]:
    """Usuário com role 'viewer' — somente leitura nos módulos permitidos."""
    return _create_user_with_role(client, db, "viewer")


@pytest.fixture
def no_role_headers(client: TestClient, db: Session) -> dict[str, str]:
    """Usuário sem nenhum role — deve ser bloqueado em qualquer módulo."""
    return _create_user_with_role(client, db, role_name=None)
