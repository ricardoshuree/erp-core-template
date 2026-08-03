# [mcp-local harness] feature: rbac-tests | plano: 34f09a59 | 2026-08-03 14:03:16
# Adiciona rota de diagnóstico /utils/rbac-check/{module_name}/{action} para testes de RBAC
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic.networks import EmailStr

from app.api.deps import get_current_active_superuser, require_module_permission
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
# Rota de diagnóstico de RBAC — usada exclusivamente pelos testes automatizados
# Não expõe dados de negócio; só verifica se o guard permite ou bloqueia o acesso.
# ---------------------------------------------------------------------------

@router.get(
    "/rbac-check/{module_name}/{action}",
    tags=["utils"],
    summary="Diagnóstico de permissão RBAC (uso interno / testes)",
)
def rbac_check(
    module_name: str,
    action: Literal["read", "edit"],
    _: Message = Depends(
        lambda module_name=module_name, action=action: require_module_permission(
            module_name, need_edit=(action == "edit")
        )
    ),
) -> Message:
    """
    Retorna 200 se o usuário autenticado tem a permissão solicitada
    no módulo informado. Usado pelos testes de RBAC para validar os
    guards sem precisar de rotas de negócio prontas.

    Códigos possíveis:
      200 — permissão concedida
      401 — não autenticado
      403 — sem permissão (role ausente ou insuficiente)
      404 — módulo não encontrado
    """
    return Message(message=f"Acesso '{action}' ao módulo '{module_name}' permitido")
