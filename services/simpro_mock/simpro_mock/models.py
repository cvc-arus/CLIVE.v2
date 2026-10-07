from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
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
    projects: Mapped[list["Project"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    statuses: Mapped[list["Status"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    assets: Mapped[list["Asset"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    given_name: Mapped[str] = mapped_column(String(255), nullable=False)
    family_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="customers")
    quotes: Mapped[list["Quote"]] = relationship(back_populates="customer")
    contacts: Mapped[list["Contact"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    sites: Mapped[list["Site"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(back_populates="customer")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    date_issued: Mapped[date | None] = mapped_column(Date, nullable=True)
    total: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="jobs")
    notes: Mapped[list["JobNote"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="quotes")
    customer: Mapped["Customer"] = relationship(back_populates="quotes")


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    given_name: Mapped[str] = mapped_column(String(255), nullable=False)
    family_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="contacts")
    customer: Mapped["Customer"] = relationship(back_populates="contacts")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postcode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    country: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="sites")
    customer: Mapped["Customer"] = relationship(back_populates="sites")
    assets: Mapped[list["Asset"]] = relationship(
        back_populates="site", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(back_populates="site")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"), nullable=False
    )
    asset_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    serial_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    installed_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="assets")
    site: Mapped["Site"] = relationship(back_populates="assets")


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


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    site_id: Mapped[int | None] = mapped_column(
        ForeignKey("sites.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="projects")
    customer: Mapped["Customer"] = relationship(back_populates="projects")
    site: Mapped["Site"] = relationship(back_populates="projects")


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
    job: Mapped["Job"] = relationship(back_populates="notes")
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
