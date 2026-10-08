"""Create the initial policy, claim and prediction tables."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_create_initial_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "polizas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.String(length=20), nullable=False),
        sa.Column("asegurado", sa.String(length=80), nullable=True),
        sa.Column("tipo", sa.String(length=10), nullable=True),
        sa.Column("prima", sa.Float(), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
        sa.Column("token_firma", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero"),
    )
    op.create_table(
        "siniestros",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("poliza_id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("monto", sa.Float(), nullable=False),
        sa.Column("descripcion", sa.String(length=200), nullable=False),
        sa.Column("estado", sa.String(length=10), server_default="abierto", nullable=False),
        sa.ForeignKeyConstraint(["poliza_id"], ["polizas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "predicciones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("poliza_id", sa.Integer(), nullable=False),
        sa.Column("puntaje", sa.Float(), nullable=False),
        sa.Column("alto_riesgo", sa.Boolean(), nullable=False),
        sa.Column("creado_en", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(["poliza_id"], ["polizas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("predicciones")
    op.drop_table("siniestros")
    op.drop_table("polizas")
