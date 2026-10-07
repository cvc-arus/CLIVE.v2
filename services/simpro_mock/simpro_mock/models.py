from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from simpro_mock.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Detail-route configuration. Simpro's company detail response documents
    # these as required; the collection response carries only ID and Name.
    # Stored flat and composed into nested wire objects by serializers.py.
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    address_line2: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    billing_address_line1: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    billing_address_line2: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    fax: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    website: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    timezone_offset: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    company_no: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    ein: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    employer_tax_ref_no: Mapped[str] = mapped_column(
        String(50), nullable=False, default=""
    )
    cis_cert_no: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    licence: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    tax_name: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    default_language: Mapped[str] = mapped_column(
        String(16), nullable=False, default="en_AU"
    )
    single_cost_center_mode: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    simpro_payments: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    template: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    multi_company_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    multi_company_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    schedule_format: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    ui_date_format: Mapped[str] = mapped_column(
        String(32), nullable=False, default="d/m/Y"
    )
    ui_time_format: Mapped[str] = mapped_column(
        String(32), nullable=False, default="H:i"
    )
    date_modified: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    zones: Mapped[list["Zone"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    customers: Mapped[list["Customer"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    quotes: Mapped[list["Quote"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    contacts: Mapped[list["Contact"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    sites: Mapped[list["Site"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    employees: Mapped[list["Employee"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    statuses: Mapped[list["Status"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    assets: Mapped[list["Asset"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


#: Sites and customers are many-to-many upstream: Site.Customers and
#: Customer.Sites are both required arrays describing the same relation.
site_customers = Table(
    "site_customers",
    Base.metadata,
    Column("site_id", ForeignKey("sites.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "customer_id",
        ForeignKey("customers.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Customer(Base):
    """A customer, either an individual or a company.

    ``type`` is the discriminator. Both name shapes are columns because the
    polymorphic collection route returns both, and the subtype detail routes
    each return one.
    """

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Kept as a column even though CompanyID left the wire: it scopes the route.
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False, default="Individual")

    # Individual names; empty for a company customer.
    given_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    family_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    cell_phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    # Company names; empty for an individual customer.
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    company_number: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    ein: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    fax: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    website: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    # Shared
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    alt_phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    customer_type: Mapped[str] = mapped_column(
        String(10), nullable=False, default="Customer"
    )
    do_not_call: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    amount_owing: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    profile_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    currency_name: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    # Address block
    address: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    country: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    # Billing address block
    billing_address: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    billing_city: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    billing_state: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    billing_postal_code: Mapped[str] = mapped_column(
        String(20), nullable=False, default=""
    )
    billing_country: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    date_created: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_modified: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="customers")
    quotes: Mapped[list["Quote"]] = relationship(back_populates="customer")
    contacts: Mapped[list["Contact"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    sites: Mapped[list["Site"]] = relationship(
        secondary=site_customers, back_populates="customers"
    )


class CustomerContract(Base):
    """A contract between a customer and the business.

    Needed as its own table because ``Job.CustomerContract`` is a **required**
    object with five required members upstream, so it can be served neither as
    ``null`` nor as ``{}``.
    """

    __tablename__ = "customer_contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contract_no: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class AssetType(Base):
    """An asset type. Upstream an asset is identified by its type, not a name."""

    __tablename__ = "asset_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    assets: Mapped[list["Asset"]] = relationship(back_populates="asset_type")


class Job(Base):
    """A job. A *project* is a job with ``type="Project"``.

    Simpro has no Projects resource, so the former ``projects`` table was
    folded into this one (ADR-013 Wave C).
    """

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Kept as a column even though CompanyID left the wire: it scopes the route.
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"), nullable=False
    )
    # A real FK, not three flat columns: a job's status draws its id from the
    # project status-code list (ADR-013 §7), so the mock cannot emit a status
    # id that exists nowhere.
    status_id: Mapped[int] = mapped_column(
        ForeignKey("statuses.id", ondelete="RESTRICT"), nullable=False
    )
    customer_contract_id: Mapped[int | None] = mapped_column(
        ForeignKey("customer_contracts.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    type: Mapped[str] = mapped_column(String(10), nullable=False, default="Service")
    stage: Mapped[str] = mapped_column(String(10), nullable=False, default="Pending")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    order_no: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    request_no: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    # Total, split by tax. Numeric(12,2), not Float: money is exact to two
    # decimal places (ADR-013).
    total_ex_tax: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    total_tax: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    total_inc_tax: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    date_issued: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_modified: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    auto_adjust_status: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    is_variation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="jobs")
    customer: Mapped["Customer"] = relationship()
    site: Mapped["Site"] = relationship()
    status: Mapped["Status"] = relationship()
    customer_contract: Mapped["CustomerContract | None"] = relationship()
    notes_list: Mapped[list["JobNote"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    custom_field_values: Mapped[list["CustomFieldValue"]] = relationship(
        primaryjoin=(
            "and_(CustomFieldValue.resource_type == 'Job', "
            "foreign(CustomFieldValue.resource_id) == Job.id)"
        ),
        viewonly=True,
    )


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Kept as a column even though CompanyID left the wire: it scopes the route.
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"), nullable=False
    )
    # Same id space as a job's status (ADR-013 §7).
    status_id: Mapped[int] = mapped_column(
        ForeignKey("statuses.id", ondelete="RESTRICT"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    type: Mapped[str] = mapped_column(String(10), nullable=False, default="Service")
    stage: Mapped[str] = mapped_column(String(12), nullable=False, default="InProgress")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    order_no: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    request_no: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    total_ex_tax: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    total_tax: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    total_inc_tax: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    date_issued: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_approved: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_modified: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    validity_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    auto_adjust_status: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    is_variation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="quotes")
    customer: Mapped["Customer"] = relationship(back_populates="quotes")
    site: Mapped["Site"] = relationship()
    status: Mapped["Status"] = relationship()
    custom_field_values: Mapped[list["CustomFieldValue"]] = relationship(
        primaryjoin=(
            "and_(CustomFieldValue.resource_type == 'Quote', "
            "foreign(CustomFieldValue.resource_id) == Quote.id)"
        ),
        viewonly=True,
    )


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Both kept as columns even though they left the wire: they scope the route.
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    given_name: Mapped[str] = mapped_column(String(255), nullable=False)
    family_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    position: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    department: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Upstream there is no single "Phone": a contact has four numbers.
    work_phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    cell_phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    alt_phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    fax: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    # The eight role flags: "is a X contact" and "is *the* X contact".
    job_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    primary_job_contact: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    quote_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    primary_quote_contact: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    invoice_contact: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    primary_invoice_contact: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    statement_contact: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    primary_statement_contact: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    date_modified: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="contacts")
    customer: Mapped["Customer"] = relationship(back_populates="contacts")


class Site(Base):
    """A customer site.

    A site belongs to *several* customers upstream, via ``site_customers``:
    ``Site.Customers`` and ``Customer.Sites`` are both required arrays and are
    the same relation. The single ``customer_id`` FK this table used to carry
    could not express that.
    """

    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Kept as a column even though CompanyID left the wire: it scopes the route.
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Address block
    address: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    country: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    # Billing address block. Upstream this one has no Country member.
    billing_address: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    billing_city: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    billing_state: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    billing_postal_code: Mapped[str] = mapped_column(
        String(20), nullable=False, default=""
    )
    billing_contact: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )

    public_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    private_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    date_modified: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    zone_id: Mapped[int | None] = mapped_column(
        ForeignKey("zones.id", ondelete="SET NULL"), nullable=True
    )
    primary_contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="sites")
    customers: Mapped[list["Customer"]] = relationship(
        secondary=site_customers, back_populates="sites"
    )
    zone: Mapped["Zone | None"] = relationship()
    primary_contact: Mapped["Contact | None"] = relationship()
    #: Read-only: custom_field_values keys on (resource_type, resource_id)
    #: rather than a real FK, because the same table serves sites, assets and
    #: jobs. The join is spelled out and viewonly so SQLAlchemy never tries to
    #: write through it.
    custom_field_values: Mapped[list["CustomFieldValue"]] = relationship(
        primaryjoin=(
            "and_(CustomFieldValue.resource_type == 'Site', "
            "foreign(CustomFieldValue.resource_id) == Site.id)"
        ),
        viewonly=True,
    )
    assets: Mapped[list["Asset"]] = relationship(
        back_populates="site", cascade="all, delete-orphan"
    )


class Asset(Base):
    """A site asset.

    Upstream an asset has no ``AssetNo``, ``Name``, ``SerialNo``, ``Model`` or
    ``Manufacturer``: it is identified by its **type**, and the serial number,
    model and manufacturer live in custom fields. That is where Simpro keeps
    CVC's CCTV asset data, which is why custom fields are in scope (ADR-013).
    """

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Kept as a column even though CompanyID left the wire: it scopes the route.
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"), nullable=False
    )
    asset_type_id: Mapped[int] = mapped_column(
        ForeignKey("asset_types.id", ondelete="RESTRICT"), nullable=False
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL"), nullable=True
    )
    customer_contract_id: Mapped[int | None] = mapped_column(
        ForeignKey("customer_contracts.id", ondelete="SET NULL"), nullable=True
    )

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    date_modified: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # LastTest is a required object with no required members, so an asset that
    # has never been tested serves {} rather than null.
    last_test_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_test_result: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="assets")
    site: Mapped["Site"] = relationship(back_populates="assets")
    asset_type: Mapped["AssetType"] = relationship(back_populates="assets")
    customer_contract: Mapped["CustomerContract | None"] = relationship()
    custom_field_values: Mapped[list["CustomFieldValue"]] = relationship(
        primaryjoin=(
            "and_(CustomFieldValue.resource_type == 'Asset', "
            "foreign(CustomFieldValue.resource_id) == Asset.id)"
        ),
        viewonly=True,
    )


class Zone(Base):
    """A service zone. Employees belong to one; sites reference one (Wave B)."""

    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="zones")
    employees: Mapped[list["Employee"]] = relationship(back_populates="default_zone")


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Kept as a column even though CompanyID left the wire: it is how
    # /companies/{id}/employees/ scopes its query.
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    # Upstream an employee has one Name, not GivenName + FamilyName.
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    # PrimaryContact, stored flat and nested by serializers.py.
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    secondary_email: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    work_phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    cell_phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    extension: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    fax: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    preferred_notification_method: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )

    # Address block, stored flat and nested by serializers.py.
    address: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    country: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    default_zone_id: Mapped[int | None] = mapped_column(
        ForeignKey("zones.id", ondelete="SET NULL"), nullable=True
    )
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    date_created: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_modified: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="employees")
    default_zone: Mapped["Zone | None"] = relationship(back_populates="employees")
    job_notes: Mapped[list["JobNote"]] = relationship(
        back_populates="submitted_by", foreign_keys="JobNote.submitted_by_id"
    )


class JobNote(Base):
    __tablename__ = "job_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Kept as a column even though JobID left the wire: it scopes the route.
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_created: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Visibility, a required object with two required booleans.
    visibility_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    visibility_customer: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Reference: what the note points at. Only Text is required upstream.
    reference_text: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    reference_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    submitted_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    assign_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="notes_list")
    submitted_by: Mapped["Employee | None"] = relationship(
        back_populates="job_notes", foreign_keys=[submitted_by_id]
    )
    assign_to: Mapped["Employee | None"] = relationship(foreign_keys=[assign_to_id])


class Attachment(Base):
    __tablename__ = "attachments"

    # A string upstream, not an integer. Opaque to callers.
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    # Kept as a column even though JobID left the wire: it scopes the route.
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    date_added: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # "Email" on the wire: whether the file rides along on outgoing email.
    email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    added_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="attachments")
    added_by: Mapped["Employee | None"] = relationship()


class CustomField(Base):
    """A custom-field *definition*: its name, type and options.

    Two tables rather than a JSON column, per ADR-013: the definition is shared
    across records and the value is per record. Simpro keeps asset serial
    numbers, models and manufacturers in custom fields, which is CVC's CCTV
    asset data, so this has to be queryable rather than opaque.
    """

    __tablename__ = "custom_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    #: Which resource the field is defined for, e.g. "Site" or "Asset".
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    #: One of List, Text, Date, Numeric, Hyperlink (Barcode too, for assets).
    field_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    #: Newline-separated options for a List field; empty otherwise.
    list_items: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Relationships
    values: Mapped[list["CustomFieldValue"]] = relationship(
        back_populates="custom_field", cascade="all, delete-orphan"
    )


class CustomFieldValue(Base):
    """One custom field's value on one record.

    ``resource_type`` + ``resource_id`` is a deliberate loose reference rather
    than a real FK: the same two tables serve sites, assets and jobs, which
    live in different tables. The mock never joins on it.
    """

    __tablename__ = "custom_field_values"

    id: Mapped[int] = mapped_column(primary_key=True)
    custom_field_id: Mapped[int] = mapped_column(
        ForeignKey("custom_fields.id", ondelete="CASCADE"), nullable=False
    )
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    custom_field: Mapped["CustomField"] = relationship(back_populates="values")


class Status(Base):
    """A project status code.

    Job and quote statuses draw their IDs from this list upstream (ADR-013 §7),
    which is why it keeps its own table rather than becoming flat columns.
    """

    __tablename__ = "statuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Kept as a column even though CompanyID left the wire: it scopes the route.
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    date_modified: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="statuses")
