# [mcp-local harness] feature: rbac-tests | plano: 3655085b | 2026-08-03 14:47:06
# conftest.py de rbac com SQLite in-memory, override de get_db e seed via init_db
"""
conftest.py — Fixtures de RBAC com SQLite in-memory.

Substitui a engine de Postgres por SQLite in-memory para rodar os testes
de RBAC sem precisar de banco externo ou Docker. Cria todas as tabelas
antes dos testes e as derruba ao final — completamente isolado do banco
de produção/desenvolvimento.

Fixtures disponíveis:
  - db            : Session SQLite in-memory com seed de roles/módulos
  - client        : TestClient apontando para a engine de teste
  - admin_headers : Bearer token de usuário com role admin
  - editor_headers: Bearer token de usuário com role editor
  - viewer_headers: Bearer token de usuário com role viewer
  - no_role_headers: Bearer token de usuário sem role
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.core.db import init_db
from app.main import app
from app.models import Role, User, UserCreate, UserRole
from app import crud
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


# ---------------------------------------------------------------------------
# Engine SQLite in-memory — compartilhada entre todos os testes da sessão
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def engine():
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(_engine)
    yield _engine
    SQLModel.metadata.drop_all(_engine)


@pytest.fixture(scope="session")
def db(engine):
    with Session(engine) as session:
        init_db(session)
        yield session


@pytest.fixture(scope="session")
def client(engine, db):
    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _create_user_with_role(
    client: TestClient,
    db: Session,
    role_name: str | None,
) -> dict[str, str]:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user: User = crud.create_user(session=db, user_create=user_in)

    if role_name is not None:
        role = db.exec(select(Role).where(Role.name == role_name)).first()
        assert role is not None, (
            f"Role '{role_name}' não encontrado — verifique se o init_db rodou"
        )
        db.add(UserRole(user_id=user.id, role_id=role.id))
        db.commit()

    return user_authentication_headers(client=client, email=email, password=password)


# ---------------------------------------------------------------------------
# Fixtures públicas de role
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_headers(client: TestClient, db: Session) -> dict[str, str]:
    return _create_user_with_role(client, db, "admin")


@pytest.fixture
def editor_headers(client: TestClient, db: Session) -> dict[str, str]:
    return _create_user_with_role(client, db, "editor")


@pytest.fixture
def viewer_headers(client: TestClient, db: Session) -> dict[str, str]:
    return _create_user_with_role(client, db, "viewer")


@pytest.fixture
def no_role_headers(client: TestClient, db: Session) -> dict[str, str]:
    return _create_user_with_role(client, db, role_name=None)
