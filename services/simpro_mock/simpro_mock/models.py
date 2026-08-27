from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from simpro_mock.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    customers: Mapped[list["Customer"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    quotes: Mapped[list["Quote"]] = relationship(
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

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    given_name = Column(String(255), nullable=False)
    family_name = Column(String(255), nullable=False)
    position = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    company = relationship("Company", backref="contacts")
    customer = relationship("Customer", backref="contacts")


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    postcode = Column(String(20), nullable=True)
    state = Column(String(50), nullable=True)
    country = Column(String(50), nullable=True)

    company = relationship("Company", backref="sites")
    customer = relationship("Customer", backref="sites")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    asset_no = Column(String(50), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    serial_no = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    manufacturer = Column(String(100), nullable=True)
    installed_date = Column(Date, nullable=True)

    company = relationship("Company", backref="assets")
    site = relationship("Site", backref="assets")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    given_name = Column(String(255), nullable=False)
    family_name = Column(String(255), nullable=False)
    position = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    company = relationship("Company", backref="employees")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    status = Column(String(100), nullable=False)
    total = Column(Float, nullable=False, default=0.0)

    company = relationship("Company", backref="projects")
    customer = relationship("Customer", backref="projects")
    site = relationship("Site", backref="projects")


class JobNote(Base):
    __tablename__ = "job_notes"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(255), nullable=True)
    note = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=True)

    job = relationship("Job", backref="notes")
    employee = relationship("Employee", backref="job_notes")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)  # in bytes
    uploaded_at = Column(DateTime, nullable=True)

    job = relationship("Job", backref="attachments")


class Status(Base):
    __tablename__ = "statuses"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=True)  # e.g., "Job", "Quote", "Project"
    is_default = Column(Integer, default=0)

    company = relationship("Company", backref="statuses")
    