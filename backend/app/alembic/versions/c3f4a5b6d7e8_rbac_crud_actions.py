# [mcp-local harness] feature: rbac-crud-permission-matrix | plano: 3c4333ee | 2026-08-04 13:42:18
# Nova migration: role_permission ganha can_create/can_update/can_delete, remove can_edit, com backfill preservando comportamento atual
"""rbac crud actions -- can_create/can_update/can_delete

Revision ID: c3f4a5b6d7e8
Revises: a1b2c3d4e5f6
Create Date: 2026-08-04

Migra role_permission de 2 booleanos (can_read/can_edit) para 4
(can_create/can_read/can_update/can_delete) -- permite expressar, por
exemplo, uma role que cria e edita mas não apaga (o padrão "Gerente").

Preserva o comportamento atual: quem tinha can_edit=True passa a ter
can_create=True, can_update=True e can_delete=True (o antigo "edit"
único cobria as três ações). can_read é copiado sem alteração.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "c3f4a5b6d7e8"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "role_permission",
        sa.Column("can_create", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "role_permission",
        sa.Column("can_update", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "role_permission",
        sa.Column("can_delete", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # Backfill: can_edit=True cobria create+update+delete no modelo antigo
    op.execute(
        "UPDATE role_permission "
        "SET can_create = can_edit, can_update = can_edit, can_delete = can_edit"
    )

    op.drop_column("role_permission", "can_edit")


def downgrade() -> None:
    op.add_column(
        "role_permission",
        sa.Column("can_edit", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Reconstrói can_edit como True se qualquer uma das 3 ações estava liberada
    op.execute(
        "UPDATE role_permission "
        "SET can_edit = (can_create OR can_update OR can_delete)"
    )
    op.drop_column("role_permission", "can_create")
    op.drop_column("role_permission", "can_update")
    op.drop_column("role_permission", "can_delete")
