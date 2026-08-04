# [mcp-local harness] feature: rbac-role-assignment-backend | plano: fde7657e | 2026-08-04 12:36:11
# Novo endpoint GET /roles/ para listar roles RBAC disponiveis, protegido por superuser
"""
Rotas de leitura das roles RBAC disponíveis (admin, editor, viewer,
mais quaisquer roles customizadas criadas depois, ex: "gerente",
"vendedor"). Só listagem -- criar/editar role e a matriz de permissão
por módulo (role_permission) ficam para uma etapa futura; hoje a
atribuição de role a usuário usa as roles já existentes (seed padrão).
"""
from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.models import Role, RolePublic, RolesPublic

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    dependencies=[Depends(get_current_active_superuser)],
)


@router.get("/", response_model=RolesPublic)
def read_roles(session: SessionDep) -> Any:
    """Lista todas as roles RBAC cadastradas, ordenadas por nome."""
    roles = session.exec(select(Role).order_by(Role.name)).all()
    return RolesPublic(data=[RolePublic.model_validate(r) for r in roles])
