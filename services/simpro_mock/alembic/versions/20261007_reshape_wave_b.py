"""reshape wave B to the published Simpro spec

Re-shapes ``customers``, ``contacts`` and ``sites`` to Simpro's published
OpenAPI contract, replaces the single ``sites.customer_id`` foreign key with a
``site_customers`` association table, and adds the two shared custom-field
tables ADR-013 decided on (Wave B).

Hand-written: ``alembic/env.py`` does not import ``simpro_mock.models``, so
``--autogenerate`` would emit drops for every table.

**On ``downgrade()``**: the container runs ``alembic upgrade head`` and
``python -m simpro_mock.seed`` on every start, and the seed truncates every
table, so a downgrade is never expected to preserve data. One step is
deliberately lossy: a site can have many customers after this migration, so
restoring the single ``sites.customer_id`` keeps only the lowest customer id
and discards the rest.

Revision ID: 4c5d6e7f8091
Revises: 3b4c5d6e7f80
Create Date: 2026-10-07 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4c5d6e7f8091"
down_revision: str | None = "3b4c5d6e7f80"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


#: ``customers`` text columns added, as ``(name, type, server_default)``.
CUSTOMER_TEXT_COLUMNS: tuple[tuple[str, sa.types.TypeEngine, str], ...] = (
    ("type", sa.String(10), "Individual"),
    ("title", sa.String(10), ""),
    ("cell_phone", sa.String(50), ""),
    ("company_name", sa.String(255), ""),
    ("company_number", sa.String(50), ""),
    ("ein", sa.String(50), ""),
    ("fax", sa.String(50), ""),
    ("website", sa.String(255), ""),
    ("alt_phone", sa.String(50), ""),
    ("customer_type", sa.String(10), "Customer"),
    ("profile_notes", sa.Text(), ""),
    ("currency_code", sa.String(10), ""),
    ("currency_name", sa.String(50), ""),
    ("address", sa.String(255), ""),
    ("city", sa.String(100), ""),
    ("state", sa.String(50), ""),
    ("postal_code", sa.String(20), ""),
    ("country", sa.String(50), ""),
    ("billing_address", sa.String(255), ""),
    ("billing_city", sa.String(100), ""),
    ("billing_state", sa.String(50), ""),
    ("billing_postal_code", sa.String(20), ""),
    ("billing_country", sa.String(50), ""),
)

#: ``contacts`` text columns added.
CONTACT_TEXT_COLUMNS: tuple[tuple[str, sa.types.TypeEngine], ...] = (
    ("title", sa.String(10)),
    ("department", sa.String(255)),
    ("notes", sa.Text()),
    ("work_phone", sa.String(50)),
    ("cell_phone", sa.String(50)),
    ("alt_phone", sa.String(50)),
    ("fax", sa.String(50)),
)

#: The eight contact-role booleans.
CONTACT_ROLE_FLAGS: tuple[str, ...] = (
    "job_contact",
    "primary_job_contact",
    "quote_contact",
    "primary_quote_contact",
    "invoice_contact",
    "primary_invoice_contact",
    "statement_contact",
    "primary_statement_contact",
)

#: ``sites`` text columns added.
SITE_TEXT_COLUMNS: tuple[tuple[str, sa.types.TypeEngine], ...] = (
    ("billing_address", sa.String(255)),
    ("billing_city", sa.String(100)),
    ("billing_state", sa.String(50)),
    ("billing_postal_code", sa.String(20)),
    ("billing_contact", sa.String(255)),
    ("public_notes", sa.Text()),
    ("private_notes", sa.Text()),
)


def upgrade() -> None:
    # ---- shared custom-field tables (Site consumes them now; Job and
    # ---- Asset follow in Wave C) ----
    op.create_table(
        "custom_fields",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("field_type", sa.String(20), nullable=False),
        sa.Column(
            "is_mandatory", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("list_items", sa.Text(), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "custom_field_values",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("custom_field_id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(32), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["custom_field_id"], ["custom_fields.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_custom_field_values_resource",
        "custom_field_values",
        ["resource_type", "resource_id"],
    )

    # ---- customers: polymorphic, with address, billing and profile blocks ----
    for name, column_type, default in CUSTOMER_TEXT_COLUMNS:
        op.add_column(
            "customers",
            sa.Column(name, column_type, nullable=False, server_default=default),
        )
        op.alter_column("customers", name, server_default=None)

    op.add_column(
        "customers",
        sa.Column(
            "do_not_call", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "customers",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "customers",
        sa.Column(
            "amount_owing", sa.Numeric(12, 2), nullable=False, server_default="0.00"
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "date_created", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "date_modified", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    for name in (
        "do_not_call",
        "archived",
        "amount_owing",
        "date_created",
        "date_modified",
    ):
        op.alter_column("customers", name, server_default=None)

    # Email and Phone are required upstream; existing rows may hold NULL.
    op.execute("UPDATE customers SET email = '' WHERE email IS NULL")
    op.execute("UPDATE customers SET phone = '' WHERE phone IS NULL")
    op.alter_column("customers", "email", existing_type=sa.String(255), nullable=False)
    op.alter_column("customers", "phone", existing_type=sa.String(50), nullable=False)

    # ---- contacts ----
    for name, column_type in CONTACT_TEXT_COLUMNS:
        op.add_column(
            "contacts",
            sa.Column(name, column_type, nullable=False, server_default=""),
        )
        op.alter_column("contacts", name, server_default=None)
    op.execute("UPDATE contacts SET work_phone = COALESCE(phone, '')")
    op.drop_column("contacts", "phone")

    for name in CONTACT_ROLE_FLAGS:
        op.add_column(
            "contacts",
            sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        op.alter_column("contacts", name, server_default=None)

    op.add_column(
        "contacts",
        sa.Column(
            "date_modified", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.alter_column("contacts", "date_modified", server_default=None)
    op.execute("UPDATE contacts SET position = '' WHERE position IS NULL")
    op.execute("UPDATE contacts SET email = '' WHERE email IS NULL")
    op.alter_column(
        "contacts", "position", existing_type=sa.String(255), nullable=False
    )
    op.alter_column("contacts", "email", existing_type=sa.String(255), nullable=False)

    # ---- sites ----
    op.alter_column("sites", "postcode", new_column_name="postal_code")
    for column in ("address", "city", "state", "postal_code", "country"):
        op.execute(f"UPDATE sites SET {column} = '' WHERE {column} IS NULL")
        op.alter_column("sites", column, existing_nullable=True, nullable=False)

    for name, column_type in SITE_TEXT_COLUMNS:
        op.add_column(
            "sites", sa.Column(name, column_type, nullable=False, server_default="")
        )
        op.alter_column("sites", name, server_default=None)

    op.add_column(
        "sites",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "sites",
        sa.Column(
            "date_modified", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.alter_column("sites", "archived", server_default=None)
    op.alter_column("sites", "date_modified", server_default=None)

    op.add_column("sites", sa.Column("zone_id", sa.Integer()))
    op.create_foreign_key(
        "fk_sites_zone_id", "sites", "zones", ["zone_id"], ["id"], ondelete="SET NULL"
    )
    op.add_column("sites", sa.Column("primary_contact_id", sa.Integer()))
    op.create_foreign_key(
        "fk_sites_primary_contact_id",
        "sites",
        "contacts",
        ["primary_contact_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ---- sites <-> customers becomes many-to-many ----
    op.create_table(
        "site_customers",
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("site_id", "customer_id"),
    )
    op.execute(
        "INSERT INTO site_customers (site_id, customer_id) "
        "SELECT id, customer_id FROM sites WHERE customer_id IS NOT NULL"
    )
    op.drop_column("sites", "customer_id")


def downgrade() -> None:
    # ---- sites <-> customers back to a single FK (lossy: keeps the lowest id)
    op.add_column("sites", sa.Column("customer_id", sa.Integer()))
    op.execute(
        "UPDATE sites SET customer_id = ("
        "  SELECT MIN(sc.customer_id) FROM site_customers sc"
        "  WHERE sc.site_id = sites.id"
        ")"
    )
    op.execute("DELETE FROM sites WHERE customer_id IS NULL")
    op.alter_column("sites", "customer_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key(
        "sites_customer_id_fkey",
        "sites",
        "customers",
        ["customer_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_table("site_customers")

    # ---- sites ----
    op.drop_constraint("fk_sites_primary_contact_id", "sites", type_="foreignkey")
    op.drop_column("sites", "primary_contact_id")
    op.drop_constraint("fk_sites_zone_id", "sites", type_="foreignkey")
    op.drop_column("sites", "zone_id")
    op.drop_column("sites", "date_modified")
    op.drop_column("sites", "archived")
    for name, _column_type in SITE_TEXT_COLUMNS:
        op.drop_column("sites", name)
    for column in ("address", "city", "state", "postal_code", "country"):
        op.alter_column("sites", column, existing_nullable=False, nullable=True)
    op.alter_column("sites", "postal_code", new_column_name="postcode")

    # ---- contacts ----
    op.alter_column("contacts", "email", existing_type=sa.String(255), nullable=True)
    op.alter_column("contacts", "position", existing_type=sa.String(255), nullable=True)
    op.drop_column("contacts", "date_modified")
    for name in CONTACT_ROLE_FLAGS:
        op.drop_column("contacts", name)
    op.add_column("contacts", sa.Column("phone", sa.String(50)))
    op.execute("UPDATE contacts SET phone = work_phone")
    for name, _column_type in CONTACT_TEXT_COLUMNS:
        op.drop_column("contacts", name)

    # ---- customers ----
    op.alter_column("customers", "phone", existing_type=sa.String(50), nullable=True)
    op.alter_column("customers", "email", existing_type=sa.String(255), nullable=True)
    for name in (
        "date_modified",
        "date_created",
        "amount_owing",
        "archived",
        "do_not_call",
    ):
        op.drop_column("customers", name)
    for name, _column_type, _default in CUSTOMER_TEXT_COLUMNS:
        op.drop_column("customers", name)

    # ---- shared custom-field tables ----
    op.drop_index("ix_custom_field_values_resource", table_name="custom_field_values")
    op.drop_table("custom_field_values")
    op.drop_table("custom_fields")
