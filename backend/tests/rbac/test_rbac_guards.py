# [mcp-local harness] feature: rbac-tests | plano: f4289c06 | 2026-08-03 14:02:45
# Testes positivos e negativos dos guards de RBAC por módulo
"""
test_rbac_guards.py — Testes dos guards require_module_permission.

Estratégia: usamos uma rota de diagnóstico em /api/v1/utils/rbac-check
que aplica os guards de leitura e edição no módulo "usuarios".
Isso permite testar o mecanismo de RBAC sem precisar de rotas de negócio
prontas — a rota de diagnóstico é a única dependência externa deste arquivo.

Cobertura:

  Positivos (HTTP 200 — acesso permitido):
    ✓ viewer  pode ler  "usuarios"
    ✓ editor  pode ler  "usuarios"
    ✓ editor  pode editar "usuarios"
    ✓ admin   pode ler  "usuarios"
    ✓ admin   pode editar "usuarios"

  Negativos (HTTP 403 — acesso bloqueado):
    ✗ viewer       NÃO pode editar "usuarios"
    ✗ sem role     NÃO pode ler    "usuarios"
    ✗ sem role     NÃO pode editar "usuarios"

  Módulo inexistente (HTTP 404):
    ✗ qualquer usuário em módulo que não existe → 404
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

API = settings.API_V1_STR

READ_URL  = f"{API}/utils/rbac-check/usuarios/read"
EDIT_URL  = f"{API}/utils/rbac-check/usuarios/edit"
GHOST_URL = f"{API}/utils/rbac-check/modulo-fantasma/read"


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

    def test_editor_can_edit(self, client: TestClient, editor_headers: dict) -> None:
        r = client.get(EDIT_URL, headers=editor_headers)
        assert r.status_code == 200

    def test_admin_can_read(self, client: TestClient, admin_headers: dict) -> None:
        r = client.get(READ_URL, headers=admin_headers)
        assert r.status_code == 200

    def test_admin_can_edit(self, client: TestClient, admin_headers: dict) -> None:
        r = client.get(EDIT_URL, headers=admin_headers)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Testes negativos — deve retornar 403
# ---------------------------------------------------------------------------

class TestRBACBlocked:
    def test_viewer_cannot_edit(self, client: TestClient, viewer_headers: dict) -> None:
        r = client.get(EDIT_URL, headers=viewer_headers)
        assert r.status_code == 403

    def test_no_role_cannot_read(self, client: TestClient, no_role_headers: dict) -> None:
        r = client.get(READ_URL, headers=no_role_headers)
        assert r.status_code == 403

    def test_no_role_cannot_edit(self, client: TestClient, no_role_headers: dict) -> None:
        r = client.get(EDIT_URL, headers=no_role_headers)
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
