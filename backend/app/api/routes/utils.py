# [mcp-local harness] feature: rbac-tests | plano: a56f90f1 | 2026-08-03 14:39:53
# Corrige rota rbac-check chamando o guard diretamente com parâmetros de path dinâmicos
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic.networks import EmailStr

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
    get_current_user,
    require_module_permission,
)
from app.models import Message
from app.utils import generate_test_email, send_email

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """Test emails."""
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True


# ---------------------------------------------------------------------------
# Rota de diagnóstico de RBAC
# Usada exclusivamente pelos testes automatizados.
# Não expõe dados de negócio — só verifica se o guard permite o acesso.
# ---------------------------------------------------------------------------

@router.get(
    "/rbac-check/{module_name}/{action}",
    summary="Diagnóstico de permissão RBAC (uso interno / testes)",
)
def rbac_check(
    module_name: str,
    action: Literal["read", "edit"],
    current_user: CurrentUser,
    session: SessionDep,
) -> Message:
    """
    Retorna 200 se o usuário autenticado tem a permissão solicitada
    no módulo informado.

    Códigos possíveis:
      200 — permissão concedida
      401 — não autenticado
      403 — sem permissão
      404 — módulo não encontrado
    """
    need_edit = action == "edit"
    # Chama o guard diretamente (não via Depends, pois module_name é dinâmico)
    checker = require_module_permission(module_name, need_edit=need_edit)
    checker(current_user=current_user, session=session)
    return Message(message=f"Acesso '{action}' ao módulo '{module_name}' permitido")
