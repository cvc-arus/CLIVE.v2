"""reshape wave A to the published Simpro spec

Re-shapes ``companies``, ``employees``, ``job_notes``, ``attachments`` and
``statuses`` to Simpro's published OpenAPI contract, and adds the ``zones``
lookup table that ``Employee.DefaultZone`` needs (ADR-013, Wave A).

Hand-written: ``alembic/env.py`` does not import ``simpro_mock.models``, so
``--autogenerate`` would emit drops for every table.

**On ``downgrade()``**: the container runs ``alembic upgrade head`` and
``python -m simpro_mock.seed`` on every start, and the seed truncates every
table, so a downgrade is never expected to preserve data. Two steps here are
deliberately lossy and would otherwise be impossible:

* ``attachments.id`` goes back from a string to an integer, so the table is
  truncated first — the seeded ids are not numeric.
* ``employees.name`` is split back into ``given_name``/``family_name`` on the
  first space, which does not round-trip for every name.

Revision ID: 3b4c5d6e7f80
Revises: 2a3b4c5d6e7f
Create Date: 2026-10-07 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3b4c5d6e7f80"
down_revision: str | None = "2a3b4c5d6e7f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


#: ``companies`` configuration columns the detail route must serve, as
#: ``(name, type, server_default)``. Every one is required upstream.
COMPANY_COLUMNS: tuple[tuple[str, sa.types.TypeEngine, str], ...] = (
    ("address_line1", sa.String(255), ""),
    ("address_line2", sa.String(255), ""),
    ("billing_address_line1", sa.String(255), ""),
    ("billing_address_line2", sa.String(255), ""),
    ("phone", sa.String(50), ""),
    ("fax", sa.String(50), ""),
    ("email", sa.String(255), ""),
    ("website", sa.String(255), ""),
    ("country", sa.String(100), ""),
    ("currency", sa.String(10), ""),
    ("timezone", sa.String(64), "UTC"),
    ("timezone_offset", sa.String(16), ""),
    ("company_no", sa.String(50), ""),
    ("ein", sa.String(50), ""),
    ("employer_tax_ref_no", sa.String(50), ""),
    ("cis_cert_no", sa.String(50), ""),
    ("licence", sa.String(100), ""),
    ("tax_name", sa.String(50), ""),
    ("default_language", sa.String(16), "en_AU"),
    ("ui_date_format", sa.String(32), "d/m/Y"),
    ("ui_time_format", sa.String(32), "H:i"),
)

#: ``employees`` columns added for ``PrimaryContact`` and ``Address``.
EMPLOYEE_TEXT_COLUMNS: tuple[tuple[str, sa.types.TypeEngine], ...] = (
    ("secondary_email", sa.String(255)),
    ("work_phone", sa.String(50)),
    ("cell_phone", sa.String(50)),
    ("extension", sa.String(20)),
    ("fax", sa.String(50)),
    ("address", sa.String(255)),
    ("city", sa.String(100)),
    ("state", sa.String(50)),
    ("postal_code", sa.String(20)),
    ("country", sa.String(50)),
)


def upgrade() -> None:
    # ---- zones (new lookup table; Site.Zone reuses it in Wave B) ----
    op.create_table(
        "zones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ---- companies: the documented configuration block ----
    for name, column_type, default in COMPANY_COLUMNS:
        op.add_column(
            "companies",
            sa.Column(name, column_type, nullable=False, server_default=default),
        )
        op.alter_column("companies", name, server_default=None)

    op.add_column(
        "companies",
        sa.Column(
            "single_cost_center_mode",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "companies",
        sa.Column(
            "simpro_payments", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "companies",
        sa.Column("template", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "companies",
        sa.Column("schedule_format", sa.Integer(), nullable=False, server_default="30"),
    )
    op.add_column(
        "companies",
        sa.Column(
            "date_modified",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column("companies", sa.Column("multi_company_label", sa.String(100)))
    op.add_column("companies", sa.Column("multi_company_color", sa.String(7)))
    for name in (
        "single_cost_center_mode",
        "simpro_payments",
        "template",
        "schedule_format",
        "date_modified",
    ):
        op.alter_column("companies", name, server_default=None)

    # ---- employees: one Name, nested contact and address ----
    op.add_column(
        "employees",
        sa.Column("name", sa.String(255), nullable=False, server_default=""),
    )
    op.execute(
        "UPDATE employees SET name = "
        "TRIM(COALESCE(given_name, '') || ' ' || COALESCE(family_name, ''))"
    )
    op.alter_column("employees", "name", server_default=None)
    op.drop_column("employees", "given_name")
    op.drop_column("employees", "family_name")

    # Position and Email are required upstream; existing rows may hold NULL.
    op.execute("UPDATE employees SET position = '' WHERE position IS NULL")
    op.execute("UPDATE employees SET email = '' WHERE email IS NULL")
    op.alter_column(
        "employees", "position", existing_type=sa.String(255), nullable=False
    )
    op.alter_column("employees", "email", existing_type=sa.String(255), nullable=False)

    for name, column_type in EMPLOYEE_TEXT_COLUMNS:
        op.add_column(
            "employees",
            sa.Column(name, column_type, nullable=False, server_default=""),
        )
        op.alter_column("employees", name, server_default=None)

    # "Phone" becomes WorkPhone inside PrimaryContact.
    op.execute("UPDATE employees SET work_phone = COALESCE(phone, '')")
    op.drop_column("employees", "phone")

    op.add_column(
        "employees", sa.Column("preferred_notification_method", sa.String(20))
    )
    op.add_column(
        "employees",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "employees",
        sa.Column(
            "date_created",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "employees",
        sa.Column(
            "date_modified",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column("employees", sa.Column("default_zone_id", sa.Integer()))
    op.create_foreign_key(
        "fk_employees_default_zone_id",
        "employees",
        "zones",
        ["default_zone_id"],
        ["id"],
        ondelete="SET NULL",
    )
    for name in ("archived", "date_created", "date_modified"):
        op.alter_column("employees", name, server_default=None)

    # ---- job_notes: Visibility, Reference, SubmittedBy, AssignTo ----
    op.alter_column("job_notes", "created_by", new_column_name="submitted_by_id")
    op.alter_column("job_notes", "created_at", new_column_name="date_created")
    op.execute("UPDATE job_notes SET date_created = now() WHERE date_created IS NULL")
    op.alter_column(
        "job_notes", "date_created", existing_type=sa.DateTime(), nullable=False
    )
    op.add_column(
        "job_notes",
        sa.Column(
            "visibility_admin", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    op.add_column(
        "job_notes",
        sa.Column(
            "visibility_customer",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "job_notes",
        sa.Column("reference_text", sa.String(255), nullable=False, server_default=""),
    )
    op.add_column("job_notes", sa.Column("reference_number", sa.String(50)))
    op.add_column("job_notes", sa.Column("reference_type", sa.String(50)))
    op.add_column("job_notes", sa.Column("follow_up_date", sa.Date()))
    op.add_column("job_notes", sa.Column("assign_to_id", sa.Integer()))
    op.create_foreign_key(
        "fk_job_notes_assign_to_id",
        "job_notes",
        "employees",
        ["assign_to_id"],
        ["id"],
        ondelete="SET NULL",
    )
    for name in (
        "visibility_admin",
        "visibility_customer",
        "reference_text",
    ):
        op.alter_column("job_notes", name, server_default=None)

    # ---- attachments: a string id, renamed size and date, new flags ----
    op.execute("ALTER TABLE attachments ALTER COLUMN id DROP DEFAULT")
    op.alter_column(
        "attachments",
        "id",
        existing_type=sa.Integer(),
        type_=sa.String(64),
        existing_nullable=False,
        postgresql_using="id::text",
    )
    op.alter_column("attachments", "file_size", new_column_name="file_size_bytes")
    op.alter_column("attachments", "uploaded_at", new_column_name="date_added")
    op.execute(
        "UPDATE attachments SET file_size_bytes = 0 WHERE file_size_bytes IS NULL"
    )
    op.execute("UPDATE attachments SET date_added = now() WHERE date_added IS NULL")
    op.execute(
        "UPDATE attachments SET mime_type = 'application/octet-stream' "
        "WHERE mime_type IS NULL"
    )
    op.alter_column(
        "attachments", "file_size_bytes", existing_type=sa.Integer(), nullable=False
    )
    op.alter_column(
        "attachments", "date_added", existing_type=sa.DateTime(), nullable=False
    )
    op.alter_column(
        "attachments", "mime_type", existing_type=sa.String(100), nullable=False
    )
    op.add_column(
        "attachments",
        sa.Column("public", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "attachments",
        sa.Column("email", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("attachments", sa.Column("added_by_id", sa.Integer()))
    op.create_foreign_key(
        "fk_attachments_added_by_id",
        "attachments",
        "employees",
        ["added_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column("attachments", "public", server_default=None)
    op.alter_column("attachments", "email", server_default=None)

    # ---- statuses: Color, Priority, DateModified replace Category/IsDefault ----
    op.drop_column("statuses", "category")
    op.drop_column("statuses", "is_default")
    op.add_column("statuses", sa.Column("color", sa.String(7)))
    op.add_column(
        "statuses",
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "statuses",
        sa.Column(
            "date_modified",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.alter_column("statuses", "priority", server_default=None)
    op.alter_column("statuses", "date_modified", server_default=None)


def downgrade() -> None:
    # ---- statuses ----
    op.drop_column("statuses", "date_modified")
    op.drop_column("statuses", "priority")
    op.drop_column("statuses", "color")
    op.add_column("statuses", sa.Column("category", sa.String(50)))
    op.add_column("statuses", sa.Column("is_default", sa.Integer(), server_default="0"))

    # ---- attachments (lossy: the string ids are not numeric) ----
    op.drop_constraint("fk_attachments_added_by_id", "attachments", type_="foreignkey")
    op.drop_column("attachments", "added_by_id")
    op.drop_column("attachments", "email")
    op.drop_column("attachments", "public")
    op.execute("TRUNCATE TABLE attachments")
    op.alter_column(
        "attachments",
        "id",
        existing_type=sa.String(64),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="id::integer",
    )
    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS attachments_id_seq OWNED BY attachments.id"
    )
    op.execute(
        "ALTER TABLE attachments ALTER COLUMN id "
        "SET DEFAULT nextval('attachments_id_seq')"
    )
    op.alter_column(
        "attachments", "mime_type", existing_type=sa.String(100), nullable=True
    )
    op.alter_column(
        "attachments", "date_added", existing_type=sa.DateTime(), nullable=True
    )
    op.alter_column(
        "attachments", "file_size_bytes", existing_type=sa.Integer(), nullable=True
    )
    op.alter_column("attachments", "date_added", new_column_name="uploaded_at")
    op.alter_column("attachments", "file_size_bytes", new_column_name="file_size")

    # ---- job_notes ----
    op.drop_constraint("fk_job_notes_assign_to_id", "job_notes", type_="foreignkey")
    op.drop_column("job_notes", "assign_to_id")
    op.drop_column("job_notes", "follow_up_date")
    op.drop_column("job_notes", "reference_type")
    op.drop_column("job_notes", "reference_number")
    op.drop_column("job_notes", "reference_text")
    op.drop_column("job_notes", "visibility_customer")
    op.drop_column("job_notes", "visibility_admin")
    op.alter_column(
        "job_notes", "date_created", existing_type=sa.DateTime(), nullable=True
    )
    op.alter_column("job_notes", "date_created", new_column_name="created_at")
    op.alter_column("job_notes", "submitted_by_id", new_column_name="created_by")

    # ---- employees (lossy: Name is split on the first space) ----
    op.drop_constraint("fk_employees_default_zone_id", "employees", type_="foreignkey")
    op.drop_column("employees", "default_zone_id")
    op.drop_column("employees", "date_modified")
    op.drop_column("employees", "date_created")
    op.drop_column("employees", "archived")
    op.drop_column("employees", "preferred_notification_method")

    op.add_column("employees", sa.Column("phone", sa.String(50)))
    op.execute("UPDATE employees SET phone = work_phone")
    for name, _column_type in EMPLOYEE_TEXT_COLUMNS:
        op.drop_column("employees", name)

    op.alter_column("employees", "email", existing_type=sa.String(255), nullable=True)
    op.alter_column(
        "employees", "position", existing_type=sa.String(255), nullable=True
    )
    op.add_column(
        "employees",
        sa.Column("given_name", sa.String(255), nullable=False, server_default=""),
    )
    op.add_column(
        "employees",
        sa.Column("family_name", sa.String(255), nullable=False, server_default=""),
    )
    op.execute("UPDATE employees SET given_name = SPLIT_PART(name, ' ', 1)")
    op.execute(
        "UPDATE employees SET family_name = "
        "TRIM(SUBSTRING(name FROM POSITION(' ' IN name || ' ')))"
    )
    op.alter_column("employees", "given_name", server_default=None)
    op.alter_column("employees", "family_name", server_default=None)
    op.drop_column("employees", "name")

    # ---- companies ----
    op.drop_column("companies", "multi_company_color")
    op.drop_column("companies", "multi_company_label")
    op.drop_column("companies", "date_modified")
    op.drop_column("companies", "schedule_format")
    op.drop_column("companies", "template")
    op.drop_column("companies", "simpro_payments")
    op.drop_column("companies", "single_cost_center_mode")
    for name, _column_type, _default in COMPANY_COLUMNS:
        op.drop_column("companies", name)

    op.drop_table("zones")
