# [mcp-local harness] feature: rbac-crud-permission-matrix | plano: 3c4333ee | 2026-08-04 13:44:27
# Testes reescritos para o modelo CRUD de 4 acoes, incluindo teste novo (editor_cannot_delete) que valida a granularidade que nao existia antes
"""
test_rbac_guards.py — Testes dos guards require_module_permission.

Estratégia: usamos uma rota de diagnóstico em /api/v1/utils/rbac-check
que aplica os guards CRUD (create/read/update/delete) no módulo
"usuarios". Isso permite testar o mecanismo de RBAC sem precisar de
rotas de negócio prontas — a rota de diagnóstico é a única dependência
externa deste arquivo.

Cobertura:

  Positivos (HTTP 200 — acesso permitido):
    ✓ viewer  pode ler (read) "usuarios"
    ✓ editor  pode ler, criar e atualizar "usuarios"
    ✓ admin   pode ler, criar, atualizar e apagar "usuarios"

  Negativos (HTTP 403 — acesso bloqueado):
    ✗ viewer  NÃO pode criar/atualizar/apagar "usuarios"
    ✗ editor  NÃO pode apagar "usuarios" -- granularidade nova: no
      modelo antigo (can_edit único) isso não era possível de expressar
    ✗ sem role NÃO pode ler nem criar "usuarios"

  Não autenticado (HTTP 401):
    ✗ sem token → 401

  Módulo inexistente (HTTP 404):
    ✗ qualquer usuário em módulo que não existe → 404
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

API = settings.API_V1_STR

READ_URL   = f"{API}/utils/rbac-check/usuarios/read"
CREATE_URL = f"{API}/utils/rbac-check/usuarios/create"
UPDATE_URL = f"{API}/utils/rbac-check/usuarios/update"
DELETE_URL = f"{API}/utils/rbac-check/usuarios/delete"
GHOST_URL  = f"{API}/utils/rbac-check/modulo-fantasma/read"


# ---------------------------------------------------------------------------
# Testes positivos
# ---------------------------------------------------------------------------

class TestRBACAllowed:
    def test_viewer_can_read(self, client: TestClient, viewer_headers: dict) -> None:
        r = client.get(READ_URL, headers=viewer_headers)
        assert r.status_code == 200

    def test_editor_can_read(self, client: TestClient, editor_headers: dict) -> None:
        r = client.get(READ_URL, headers=editor_headers)
        assert r.status_code == 200

    def test_editor_can_create(self, client: TestClient, editor_headers: dict) -> None:
        r = client.get(CREATE_URL, headers=editor_headers)
        assert r.status_code == 200

    def test_editor_can_update(self, client: TestClient, editor_headers: dict) -> None:
        r = client.get(UPDATE_URL, headers=editor_headers)
        assert r.status_code == 200

    def test_admin_can_read(self, client: TestClient, admin_headers: dict) -> None:
        r = client.get(READ_URL, headers=admin_headers)
        assert r.status_code == 200

    def test_admin_can_create(self, client: TestClient, admin_headers: dict) -> None:
        r = client.get(CREATE_URL, headers=admin_headers)
        assert r.status_code == 200

    def test_admin_can_update(self, client: TestClient, admin_headers: dict) -> None:
        r = client.get(UPDATE_URL, headers=admin_headers)
        assert r.status_code == 200

    def test_admin_can_delete(self, client: TestClient, admin_headers: dict) -> None:
        r = client.get(DELETE_URL, headers=admin_headers)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Testes negativos — deve retornar 403
# ---------------------------------------------------------------------------

class TestRBACBlocked:
    def test_viewer_cannot_create(self, client: TestClient, viewer_headers: dict) -> None:
        r = client.get(CREATE_URL, headers=viewer_headers)
        assert r.status_code == 403

    def test_viewer_cannot_update(self, client: TestClient, viewer_headers: dict) -> None:
        r = client.get(UPDATE_URL, headers=viewer_headers)
        assert r.status_code == 403

    def test_viewer_cannot_delete(self, client: TestClient, viewer_headers: dict) -> None:
        r = client.get(DELETE_URL, headers=viewer_headers)
        assert r.status_code == 403

    def test_editor_cannot_delete(self, client: TestClient, editor_headers: dict) -> None:
        """
        Granularidade nova: editor tem create/read/update mas NÃO
        delete (padrão "Gerente"). No modelo antigo (can_edit único)
        esse cenário não existia -- can_edit=True liberava tudo.
        """
        r = client.get(DELETE_URL, headers=editor_headers)
        assert r.status_code == 403

    def test_no_role_cannot_read(self, client: TestClient, no_role_headers: dict) -> None:
        r = client.get(READ_URL, headers=no_role_headers)
        assert r.status_code == 403

    def test_no_role_cannot_create(self, client: TestClient, no_role_headers: dict) -> None:
        r = client.get(CREATE_URL, headers=no_role_headers)
        assert r.status_code == 403

    def test_unauthenticated_cannot_read(self, client: TestClient) -> None:
        r = client.get(READ_URL)
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Módulo inexistente — deve retornar 404
# ---------------------------------------------------------------------------

class TestRBACModuleNotFound:
    def test_ghost_module_returns_404(
        self, client: TestClient, admin_headers: dict
    ) -> None:
        r = client.get(GHOST_URL, headers=admin_headers)
        assert r.status_code == 404
