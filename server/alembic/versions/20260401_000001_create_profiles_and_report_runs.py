"""create profiles and report runs tables"""

from alembic import op
import sqlalchemy as sa


revision = "20260401_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_profiles_id"), "profiles", ["id"], unique=False)
    op.create_index(op.f("ix_profiles_normalized_name"), "profiles", ["normalized_name"], unique=True)
    op.create_table(
        "report_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("zone_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_zone_name", sa.String(length=255), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("source_file_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("report_filename", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("schema_version", sa.String(length=50), nullable=True),
        sa.Column("detected_period_label", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_report_runs_id"), "report_runs", ["id"], unique=False)
    op.create_index("ix_report_runs_profile_created", "report_runs", ["profile_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_report_runs_profile_created", table_name="report_runs")
    op.drop_index(op.f("ix_report_runs_id"), table_name="report_runs")
    op.drop_table("report_runs")
    op.drop_index(op.f("ix_profiles_normalized_name"), table_name="profiles")
    op.drop_index(op.f("ix_profiles_id"), table_name="profiles")
    op.drop_table("profiles")

