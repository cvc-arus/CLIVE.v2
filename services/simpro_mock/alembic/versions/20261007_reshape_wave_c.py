"""reshape wave C to the published Simpro spec

Re-shapes ``jobs``, ``quotes`` and ``assets``, adds the ``asset_types`` and
``customer_contracts`` lookup tables, converts money from ``Float`` to
``Numeric(12, 2)``, and **drops the ``projects`` table** after folding its rows
into ``jobs`` as ``type = 'Project'`` (ADR-013 Wave C).

Simpro has no Projects resource: a project is a job with ``Type: "Project"``.
The table has had no route since S2 and now has no model either.

``jobs.status_id`` and ``quotes.status_id`` are real foreign keys to
``statuses``, not flat text columns. The contract documents the ``Status``
field of the Job and Quote write bodies as "ID of a project status code", so
these share an id space with ``/setup/statusCodes/projects/``; flat columns
would let the mock emit a status id that exists nowhere.

Hand-written: ``alembic/env.py`` does not import ``simpro_mock.models``, so
``--autogenerate`` would emit drops for every table.

**On ``downgrade()``**: the container runs ``alembic upgrade head`` and
``python -m simpro_mock.seed`` on every start, and the seed truncates every
table, so a downgrade is never expected to preserve data. Three steps are
deliberately lossy:

* ``projects`` is recreated **empty** — the converted jobs are not split back
  out, because nothing records which jobs came from projects.
* ``assets`` is truncated before ``asset_no`` returns, since that column was
  dropped and its values are gone; it is ``NOT NULL UNIQUE``.
* the money columns go back to ``Float``, which cannot represent every
  two-decimal value exactly.

Revision ID: 5d6e7f809102
Revises: 4c5d6e7f8091
Create Date: 2026-10-07 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5d6e7f809102"
down_revision: str | None = "4c5d6e7f8091"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


#: Money columns added to both ``jobs`` and ``quotes``.
MONEY_COLUMNS: tuple[str, ...] = ("total_ex_tax", "total_tax", "total_inc_tax")

#: Text columns added to both ``jobs`` and ``quotes``, as ``(name, type)``.
SHARED_TEXT_COLUMNS: tuple[tuple[str, sa.types.TypeEngine], ...] = (
    ("description", sa.String(255)),
    ("notes", sa.Text()),
    ("order_no", sa.String(50)),
    ("request_no", sa.String(50)),
)


def _add_shared_columns(table: str, default_stage: str) -> None:
    """Add the columns ``jobs`` and ``quotes`` have in common."""
    for name, column_type in SHARED_TEXT_COLUMNS:
        op.add_column(
            table, sa.Column(name, column_type, nullable=False, server_default="")
        )
        op.alter_column(table, name, server_default=None)

    op.add_column(
        table,
        sa.Column("type", sa.String(10), nullable=False, server_default="Service"),
    )
    op.add_column(
        table,
        sa.Column("stage", sa.String(12), nullable=False, server_default=default_stage),
    )
    op.add_column(
        table,
        sa.Column(
            "auto_adjust_status", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    op.add_column(
        table,
        sa.Column(
            "is_variation", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        table,
        sa.Column(
            "date_modified", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    for name in (
        "type",
        "stage",
        "auto_adjust_status",
        "is_variation",
        "date_modified",
    ):
        op.alter_column(table, name, server_default=None)

    for name in MONEY_COLUMNS:
        op.add_column(
            table,
            sa.Column(name, sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        )
        op.alter_column(table, name, server_default=None)


def upgrade() -> None:
    # ---- lookup tables ----
    op.create_table(
        "asset_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "customer_contracts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contract_no", sa.String(50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ---- jobs ----
    _add_shared_columns("jobs", "Pending")
    op.execute("UPDATE jobs SET description = name")
    op.execute("UPDATE jobs SET total_inc_tax = COALESCE(total, 0)")
    op.drop_column("jobs", "total")

    op.add_column("jobs", sa.Column("customer_id", sa.Integer()))
    op.add_column("jobs", sa.Column("site_id", sa.Integer()))
    op.add_column("jobs", sa.Column("status_id", sa.Integer()))
    op.add_column("jobs", sa.Column("customer_contract_id", sa.Integer()))
    op.add_column("jobs", sa.Column("due_date", sa.Date()))
    op.add_column("jobs", sa.Column("completed_date", sa.Date()))

    # Point existing rows at a real customer, site and status before the
    # columns become NOT NULL. The seed truncates and rebuilds anyway; this is
    # only so the migration survives a populated database.
    op.execute(
        "UPDATE jobs SET customer_id = ("
        "  SELECT MIN(c.id) FROM customers c WHERE c.company_id = jobs.company_id"
        ")"
    )
    op.execute(
        "UPDATE jobs SET site_id = ("
        "  SELECT MIN(s.id) FROM sites s WHERE s.company_id = jobs.company_id"
        ")"
    )
    op.execute(
        "UPDATE jobs SET status_id = ("
        "  SELECT MIN(st.id) FROM statuses st WHERE st.company_id = jobs.company_id"
        ")"
    )
    op.execute(
        "DELETE FROM jobs WHERE customer_id IS NULL OR site_id IS NULL "
        "OR status_id IS NULL"
    )
    for name in ("customer_id", "site_id", "status_id"):
        op.alter_column("jobs", name, existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key(
        "fk_jobs_customer_id",
        "jobs",
        "customers",
        ["customer_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_jobs_site_id", "jobs", "sites", ["site_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_jobs_status_id",
        "jobs",
        "statuses",
        ["status_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_jobs_customer_contract_id",
        "jobs",
        "customer_contracts",
        ["customer_contract_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_column("jobs", "status")

    # ---- projects fold into jobs, then the table goes ----
    op.execute(
        "INSERT INTO jobs ("
        "  company_id, customer_id, site_id, status_id, name, description,"
        "  type, stage, notes, order_no, request_no,"
        "  total_ex_tax, total_tax, total_inc_tax, date_modified,"
        "  auto_adjust_status, is_variation"
        ") SELECT "
        "  p.company_id, p.customer_id,"
        "  COALESCE(p.site_id, (SELECT MIN(s.id) FROM sites s"
        "    WHERE s.company_id = p.company_id)),"
        "  (SELECT MIN(st.id) FROM statuses st WHERE st.company_id = p.company_id),"
        "  p.name, p.name, 'Project', 'Pending', '', '', '',"
        "  0, 0, COALESCE(p.total, 0), now(), true, false"
        " FROM projects p"
        " WHERE p.customer_id IS NOT NULL"
        "   AND EXISTS (SELECT 1 FROM sites s WHERE s.company_id = p.company_id)"
        "   AND EXISTS (SELECT 1 FROM statuses st WHERE st.company_id = p.company_id)"
    )
    op.drop_table("projects")

    # ---- quotes ----
    _add_shared_columns("quotes", "InProgress")
    op.execute("UPDATE quotes SET description = name")
    op.execute("UPDATE quotes SET total_inc_tax = COALESCE(total, 0)")
    op.drop_column("quotes", "total")

    op.add_column("quotes", sa.Column("site_id", sa.Integer()))
    op.add_column("quotes", sa.Column("status_id", sa.Integer()))
    op.add_column("quotes", sa.Column("date_issued", sa.Date()))
    op.add_column("quotes", sa.Column("date_approved", sa.Date()))
    op.add_column("quotes", sa.Column("due_date", sa.Date()))
    op.add_column(
        "quotes",
        sa.Column("validity_days", sa.Integer(), nullable=False, server_default="30"),
    )
    op.add_column(
        "quotes",
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("quotes", "validity_days", server_default=None)
    op.alter_column("quotes", "is_closed", server_default=None)

    op.execute(
        "UPDATE quotes SET customer_id = ("
        "  SELECT MIN(c.id) FROM customers c WHERE c.company_id = quotes.company_id"
        ") WHERE customer_id IS NULL"
    )
    op.execute(
        "UPDATE quotes SET site_id = ("
        "  SELECT MIN(s.id) FROM sites s WHERE s.company_id = quotes.company_id"
        ")"
    )
    op.execute(
        "UPDATE quotes SET status_id = ("
        "  SELECT MIN(st.id) FROM statuses st WHERE st.company_id = quotes.company_id"
        ")"
    )
    op.execute(
        "DELETE FROM quotes WHERE customer_id IS NULL OR site_id IS NULL "
        "OR status_id IS NULL"
    )
    for name in ("customer_id", "site_id", "status_id"):
        op.alter_column("quotes", name, existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key(
        "fk_quotes_site_id", "quotes", "sites", ["site_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_quotes_status_id",
        "quotes",
        "statuses",
        ["status_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_column("quotes", "status")

    # ---- assets ----
    op.add_column("assets", sa.Column("asset_type_id", sa.Integer()))
    op.add_column("assets", sa.Column("parent_id", sa.Integer()))
    op.add_column("assets", sa.Column("customer_contract_id", sa.Integer()))
    op.add_column("assets", sa.Column("start_date", sa.Date()))
    op.add_column(
        "assets",
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "assets",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "assets",
        sa.Column(
            "date_modified", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.add_column("assets", sa.Column("last_test_date", sa.Date()))
    op.add_column("assets", sa.Column("last_test_result", sa.String(50)))
    for name in ("display_order", "archived", "date_modified"):
        op.alter_column("assets", name, server_default=None)

    # One asset type per distinct manufacturer+model, so existing rows keep a
    # meaningful type rather than all collapsing onto one.
    op.execute(
        "INSERT INTO asset_types (company_id, name) "
        "SELECT DISTINCT a.company_id, COALESCE(NULLIF(a.name, ''), 'Asset') "
        "FROM assets a"
    )
    op.execute(
        "UPDATE assets SET asset_type_id = ("
        "  SELECT MIN(t.id) FROM asset_types t"
        "  WHERE t.company_id = assets.company_id"
        "    AND t.name = COALESCE(NULLIF(assets.name, ''), 'Asset')"
        ")"
    )
    op.execute("UPDATE assets SET start_date = COALESCE(installed_date, CURRENT_DATE)")
    op.execute("DELETE FROM assets WHERE asset_type_id IS NULL")
    op.alter_column(
        "assets", "asset_type_id", existing_type=sa.Integer(), nullable=False
    )
    op.alter_column("assets", "start_date", existing_type=sa.Date(), nullable=False)
    op.create_foreign_key(
        "fk_assets_asset_type_id",
        "assets",
        "asset_types",
        ["asset_type_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_assets_parent_id",
        "assets",
        "assets",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_assets_customer_contract_id",
        "assets",
        "customer_contracts",
        ["customer_contract_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # The serial number, model and manufacturer move into custom fields.
    op.drop_constraint("assets_asset_no_key", "assets", type_="unique")
    for name in (
        "asset_no",
        "name",
        "serial_no",
        "model",
        "manufacturer",
        "installed_date",
    ):
        op.drop_column("assets", name)


def downgrade() -> None:
    # ---- assets (lossy: asset_no is NOT NULL UNIQUE and its values are gone)
    op.execute("TRUNCATE TABLE assets CASCADE")
    op.add_column("assets", sa.Column("asset_no", sa.String(50), nullable=False))
    op.add_column("assets", sa.Column("name", sa.String(255), nullable=False))
    op.add_column("assets", sa.Column("serial_no", sa.String(100)))
    op.add_column("assets", sa.Column("model", sa.String(100)))
    op.add_column("assets", sa.Column("manufacturer", sa.String(100)))
    op.add_column("assets", sa.Column("installed_date", sa.Date()))
    op.create_unique_constraint("assets_asset_no_key", "assets", ["asset_no"])

    op.drop_constraint("fk_assets_customer_contract_id", "assets", type_="foreignkey")
    op.drop_constraint("fk_assets_parent_id", "assets", type_="foreignkey")
    op.drop_constraint("fk_assets_asset_type_id", "assets", type_="foreignkey")
    for name in (
        "last_test_result",
        "last_test_date",
        "date_modified",
        "archived",
        "display_order",
        "start_date",
        "customer_contract_id",
        "parent_id",
        "asset_type_id",
    ):
        op.drop_column("assets", name)

    # ---- quotes ----
    op.add_column(
        "quotes", sa.Column("status", sa.String(100), nullable=False, server_default="")
    )
    op.alter_column("quotes", "status", server_default=None)
    op.drop_constraint("fk_quotes_status_id", "quotes", type_="foreignkey")
    op.drop_constraint("fk_quotes_site_id", "quotes", type_="foreignkey")
    op.alter_column("quotes", "customer_id", existing_type=sa.Integer(), nullable=True)
    op.add_column(
        "quotes", sa.Column("total", sa.Float(), nullable=False, server_default="0")
    )
    op.execute("UPDATE quotes SET total = total_inc_tax")
    op.alter_column("quotes", "total", server_default=None)
    for name in (
        "is_closed",
        "validity_days",
        "due_date",
        "date_approved",
        "date_issued",
        "status_id",
        "site_id",
    ):
        op.drop_column("quotes", name)
    _drop_shared_columns("quotes")

    # ---- projects, recreated empty ----
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(100), nullable=False),
        sa.Column("total", sa.Float(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("DELETE FROM jobs WHERE type = 'Project'")

    # ---- jobs ----
    op.add_column(
        "jobs", sa.Column("status", sa.String(100), nullable=False, server_default="")
    )
    op.alter_column("jobs", "status", server_default=None)
    op.drop_constraint("fk_jobs_customer_contract_id", "jobs", type_="foreignkey")
    op.drop_constraint("fk_jobs_status_id", "jobs", type_="foreignkey")
    op.drop_constraint("fk_jobs_site_id", "jobs", type_="foreignkey")
    op.drop_constraint("fk_jobs_customer_id", "jobs", type_="foreignkey")
    op.add_column(
        "jobs", sa.Column("total", sa.Float(), nullable=False, server_default="0")
    )
    op.execute("UPDATE jobs SET total = total_inc_tax")
    op.alter_column("jobs", "total", server_default=None)
    for name in (
        "completed_date",
        "due_date",
        "customer_contract_id",
        "status_id",
        "site_id",
        "customer_id",
    ):
        op.drop_column("jobs", name)
    _drop_shared_columns("jobs")

    # ---- lookup tables ----
    op.drop_table("customer_contracts")
    op.drop_table("asset_types")


def _drop_shared_columns(table: str) -> None:
    """Reverse :func:`_add_shared_columns`."""
    for name in MONEY_COLUMNS:
        op.drop_column(table, name)
    for name in (
        "date_modified",
        "is_variation",
        "auto_adjust_status",
        "stage",
        "type",
    ):
        op.drop_column(table, name)
    for name, _column_type in SHARED_TEXT_COLUMNS:
        op.drop_column(table, name)
