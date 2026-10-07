# simpro_mock/seed.py

import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from simpro_mock.database import Base, SessionLocal
from simpro_mock.models import (
    Asset,
    Attachment,
    Company,
    Contact,
    Customer,
    CustomField,
    CustomFieldValue,
    Employee,
    Job,
    JobNote,
    Project,
    Quote,
    Site,
    Status,
    Zone,
)

# Fixed seed so every start produces identical data (same day; see seed_data).
RANDOM_SEED = 42


def truncate_tables(db: Session):
    """Truncate every mapped table and reset identity sequences.

    Driven off ``Base.metadata`` rather than a hardcoded list, so a table added
    in a later migration cannot be silently missed — which matters for the
    ADR-013 re-shape, where three waves each add tables. ``sorted_tables`` is
    dependency-ordered (parents first), so it is reversed to delete children
    first; ``CASCADE`` would cover it either way.
    """
    tables = [table.name for table in reversed(Base.metadata.sorted_tables)]
    for table in tables:
        db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
    db.commit()
    print(f"✅ All {len(tables)} tables truncated.")


def get_or_create_company(db: Session, name: str, now: datetime) -> Company:
    """Create a company with the configuration block its detail route serves.

    Every field below is required by Simpro's company detail response
    (ADR-013), so the mock has to hold a real value for each one rather than
    leaving it null.
    """
    company = db.query(Company).filter(Company.name == name).first()
    if not company:
        slug = name.lower().replace(" ", "")
        company = Company(
            name=name,
            address_line1="Level 2",
            address_line2="140 Queen Street",
            billing_address_line1="PO Box 1234",
            billing_address_line2="Melbourne VIC 3001",
            phone="03 9000 0000",
            fax="03 9000 0001",
            email=f"accounts@{slug}.com.au",
            website=f"https://www.{slug}.com.au",
            country="Australia",
            currency="AUD",
            timezone="Australia/Melbourne",
            timezone_offset="+10:00",
            company_no="ACN 000 000 000",
            ein="",
            employer_tax_ref_no="",
            cis_cert_no="",
            licence="SEC-LIC-00000",
            tax_name="GST",
            default_language="en_AU",
            single_cost_center_mode=True,
            simpro_payments=False,
            template=False,
            multi_company_label=name,
            multi_company_color="#1f6feb",
            schedule_format=30,
            ui_date_format="d/m/Y",
            ui_time_format="H:i",
            date_modified=now,
        )
        db.add(company)
        db.flush()
    return company


def seed_data():
    random.seed(RANDOM_SEED)
    # Anchor timestamps to midnight today so restarts on the same day match.
    seed_now = datetime.combine(date.today(), time.min)
    db = SessionLocal()

    # --- Clear existing data ---
    truncate_tables(db)

    # ---- 1. Companies ----
    companies = [
        get_or_create_company(db, "CVC Service", seed_now),
        get_or_create_company(db, "CVC Projects", seed_now),
    ]
    db.commit()

    # ---- 1b. Zones (Employee.DefaultZone; Site.Zone reuses these in Wave B) ----
    zone_names = ["Metro North", "Metro South", "Regional"]
    for company in companies:
        for zone_name in zone_names:
            db.add(Zone(company_id=company.id, name=zone_name))
    db.commit()

    # ---- 2. Customers (16) ----
    customer_data = [
        ("John", "Smith", "john.smith@example.com", "0412345678"),
        ("Jane", "Doe", "jane.doe@example.com", "0412345679"),
        ("Bob", "Johnson", "bob.j@example.com", "0412345680"),
        ("Alice", "Williams", "alice.w@example.com", "0412345681"),
        ("Charlie", "Brown", "charlie.b@example.com", "0412345682"),
        ("Eva", "Green", "eva.g@example.com", "0412345683"),
        ("David", "Miller", "david.m@example.com", "0412345684"),
        ("Sophie", "Taylor", "sophie.t@example.com", "0412345685"),
        ("George", "Harris", "george.h@example.com", "0412345686"),
        ("Nora", "Owens", "nora.o@example.com", "0412345687"),
        ("Liam", "Nelson", "liam.n@example.com", "0412345688"),
        ("Mia", "Carter", "mia.c@example.com", "0412345689"),
        ("Noah", "Parker", "noah.p@example.com", "0412345690"),
        ("Emma", "Cooper", "emma.c@example.com", "0412345691"),
        ("Oliver", "Reed", "oliver.r@example.com", "0412345692"),
        ("Amelia", "Bennett", "amelia.b@example.com", "0412345693"),
    ]
    company_customer_names = [
        "Acme Property Group",
        "Harbour Retail Pty Ltd",
        "Northside Logistics",
        "Riverside Medical Centre",
        "Summit Education Trust",
        "Ironbark Manufacturing",
        "Bluewater Hospitality",
        "Granite Facilities Management",
    ]
    customers = []
    for company in companies:
        for index in range(8):  # 8 per company = total 16
            first, last, email, phone = customer_data.pop(0)
            # Alternate the two kinds so both subtype routes have data.
            is_company = index % 2 == 1
            city = random.choice(["Brisbane", "Sydney", "Melbourne", "Perth"])
            state = random.choice(["QLD", "NSW", "VIC", "WA"])
            postal_code = f"{random.randint(2000, 7000)}"
            cust = Customer(
                company_id=company.id,
                type="Company" if is_company else "Individual",
                given_name="" if is_company else first,
                family_name="" if is_company else last,
                title="" if is_company else random.choice(["Mr", "Ms", "Dr"]),
                cell_phone="" if is_company else phone,
                company_name=(
                    company_customer_names.pop(0) if is_company else ""
                ),
                company_number=f"ACN {random.randint(100, 999)} 000 000"
                if is_company
                else "",
                ein="",
                fax="",
                website=f"https://www.example{index}.com.au" if is_company else "",
                email=email,
                phone=phone,
                alt_phone="",
                customer_type="Customer",
                do_not_call=False,
                archived=False,
                amount_owing=Decimal(
                    f"{random.randint(0, 9999)}.{random.randint(0, 99):02d}"
                ),
                profile_notes="",
                currency_code="AUD",
                currency_name="Australian Dollar",
                address=f"{random.randint(1, 999)} Example Street",
                city=city,
                state=state,
                postal_code=postal_code,
                country="Australia",
                billing_address=f"PO Box {random.randint(1, 999)}",
                billing_city=city,
                billing_state=state,
                billing_postal_code=postal_code,
                billing_country="Australia",
                date_created=seed_now - timedelta(days=random.randint(100, 1200)),
                date_modified=seed_now - timedelta(days=random.randint(0, 60)),
            )
            db.add(cust)
            customers.append(cust)
    db.commit()

    # ---- 3. Contacts (24) ----
    positions = [
        "Site Manager",
        "Accounts Contact",
        "Facilities Manager",
        "Operations Manager",
        "Project Coordinator",
    ]
    for customer in customers:
        for pos in random.sample(positions, k=3):
            surname = customer.family_name or customer.company_name.split()[0]
            contact = Contact(
                company_id=customer.company_id,
                customer_id=customer.id,
                given_name=f"Contact_{pos.replace(' ', '_')}_{customer.id}",
                family_name=surname,
                title=random.choice(["Mr", "Ms", "Dr"]),
                position=pos,
                department=random.choice(
                    ["Operations", "Finance", "Facilities", "Projects"]
                ),
                email=f"{pos.replace(' ', '.')}.{surname}@example.com",
                notes="",
                work_phone=f"04{random.randint(10000000, 99999999)}",
                cell_phone=f"04{random.randint(10000000, 99999999)}",
                alt_phone="",
                fax="",
                job_contact=pos == "Site Manager",
                primary_job_contact=pos == "Site Manager",
                quote_contact=pos == "Project Coordinator",
                primary_quote_contact=pos == "Project Coordinator",
                invoice_contact=pos == "Accounts Contact",
                primary_invoice_contact=pos == "Accounts Contact",
                statement_contact=pos == "Accounts Contact",
                primary_statement_contact=pos == "Accounts Contact",
                date_modified=seed_now - timedelta(days=random.randint(0, 45)),
            )
            db.add(contact)
    db.commit()

    # ---- 4. Sites (16) ----
    site_names = [
        "Smith Residence",
        "Doe Office",
        "Johnson Warehouse",
        "Williams Retail",
        "Brown Factory",
        "Green Depot",
        "Miller Medical",
        "Taylor School",
        "Harris Estate",
        "Owens Tower",
        "Nelson Complex",
        "Carter Plaza",
        "Parker Centre",
        "Cooper Court",
        "Reed Gardens",
        "Bennett House",
    ]
    cities = ["Brisbane", "Sydney", "Melbourne", "Perth", "Adelaide"]
    states = ["QLD", "NSW", "VIC", "WA", "SA"]
    for company in companies:
        company_customers = [c for c in customers if c.company_id == company.id]
        company_zones = db.query(Zone).filter(Zone.company_id == company.id).all()
        for _ in range(8):
            cust = random.choice(company_customers)
            city = random.choice(cities)
            state = random.choice(states)
            postal_code = f"{random.randint(2000, 7000)}"
            street = (
                f"{random.randint(1, 999)} "
                f"{random.choice(['Main', 'Park', 'Queen', 'George', 'Albert'])} "
                f"{random.choice(['St', 'Ave', 'Rd', 'Blvd'])}"
            )
            site = Site(
                company_id=company.id,
                name=site_names.pop(0),
                address=street,
                city=city,
                state=state,
                postal_code=postal_code,
                country="Australia",
                billing_address=f"PO Box {random.randint(1, 999)}",
                billing_city=city,
                billing_state=state,
                billing_postal_code=postal_code,
                billing_contact="Accounts Payable",
                public_notes="",
                private_notes="",
                archived=False,
                zone_id=random.choice(company_zones).id,
                date_modified=seed_now - timedelta(days=random.randint(0, 60)),
            )
            # Site.Customers is a required array upstream, so every site is
            # linked to at least one customer through the association table.
            site.customers.append(cust)
            db.add(site)
    db.commit()

    # ---- 4b. Each site's primary contact, taken from one of its customers ----
    for site in db.query(Site).order_by(Site.id).all():
        owner = site.customers[0] if site.customers else None
        if owner and owner.contacts:
            site.primary_contact_id = owner.contacts[0].id
    db.commit()

    # ---- 4c. Custom fields (Site now; Job and Asset in Wave C) ----
    site_field_names = [
        ("Alarm Code", "Text"),
        ("Access Notes", "Text"),
        ("Site Category", "List"),
    ]
    for company in companies:
        for field_name, field_type in site_field_names:
            db.add(
                CustomField(
                    company_id=company.id,
                    resource_type="Site",
                    name=field_name,
                    field_type=field_type,
                    is_mandatory=False,
                    list_items=(
                        "Commercial\nResidential\nIndustrial"
                        if field_type == "List"
                        else ""
                    ),
                )
            )
    db.commit()

    for site in db.query(Site).order_by(Site.id).all():
        definitions = (
            db.query(CustomField)
            .filter(
                CustomField.company_id == site.company_id,
                CustomField.resource_type == "Site",
            )
            .order_by(CustomField.id)
            .all()
        )
        for definition in definitions:
            if definition.field_type == "List":
                value = random.choice(definition.list_items.split("\n"))
            else:
                value = f"{definition.name} for site {site.id}"
            db.add(
                CustomFieldValue(
                    custom_field_id=definition.id,
                    resource_type="Site",
                    resource_id=site.id,
                    value=value,
                )
            )
    db.commit()

    # ---- 5. Employees (12) ----
    employee_data = [
        ("Sarah", "Williams", "Project Manager"),
        ("Michael", "Chen", "Security Technician"),
        ("James", "Davis", "Electrician"),
        ("Emily", "Jones", "Estimator"),
        ("Daniel", "Kim", "Administrator"),
        ("Laura", "Martinez", "Senior Technician"),
        ("Robert", "Wilson", "Field Supervisor"),
        ("Karen", "Anderson", "Operations Manager"),
        ("Thomas", "Taylor", "Installation Lead"),
        ("Jessica", "Brown", "Support Coordinator"),
        ("Andrew", "White", "Compliance Officer"),
        ("Olivia", "Black", "Systems Integrator"),
    ]
    for company in companies:
        company_zones = db.query(Zone).filter(Zone.company_id == company.id).all()
        for emp in employee_data[:6]:  # 6 per company = total 12
            given, family, pos = emp
            employee = Employee(
                company_id=company.id,
                name=f"{given} {family}",
                position=pos,
                email=f"{given.lower()}.{family.lower()}@cvc.com.au",
                secondary_email="",
                work_phone=f"04{random.randint(10000000, 99999999)}",
                cell_phone=f"04{random.randint(10000000, 99999999)}",
                extension=str(random.randint(100, 999)),
                fax="",
                preferred_notification_method="Email",
                address=f"{random.randint(1, 200)} Collins Street",
                city="Melbourne",
                state="VIC",
                postal_code="3000",
                country="Australia",
                default_zone_id=random.choice(company_zones).id,
                archived=False,
                date_created=seed_now - timedelta(days=random.randint(200, 900)),
                date_modified=seed_now - timedelta(days=random.randint(0, 30)),
            )
            db.add(employee)
    db.commit()

    # ---- 6. Statuses (12) ----
    status_names = [
        ("Pending", "Job"),
        ("Approved", "Job"),
        ("In Progress", "Job"),
        ("Complete", "Job"),
        ("On Hold", "Job"),
        ("Cancelled", "Job"),
        ("Draft", "Quote"),
        ("Sent", "Quote"),
        ("Accepted", "Quote"),
        ("Rejected", "Quote"),
        ("Planning", "Project"),
        ("Closed", "Project"),
    ]
    status_colors = [
        "#6e7781",
        "#1f6feb",
        "#bf8700",
        "#1a7f37",
        "#9a6700",
        "#cf222e",
        "#8250df",
        "#0969da",
        "#1a7f37",
        "#cf222e",
        "#6e7781",
        "#24292f",
    ]
    for company in companies:
        for priority, (name, _category) in enumerate(status_names, start=1):
            status = Status(
                company_id=company.id,
                name=name,
                color=status_colors[priority - 1],
                priority=priority,
                date_modified=seed_now - timedelta(days=random.randint(0, 60)),
            )
            db.add(status)
    db.commit()

    # ---- 7. Assets (40) ----
    asset_types = [
        ("Hikvision Dome Camera", "DS-2CD2347G2-LU", "Hikvision"),
        ("Axis Network Camera", "P3265-LV", "Axis"),
        ("Access Control Panel", "AC-2000", "HID"),
        ("Fire Alarm Panel", "FACP-5000", "Notifier"),
        ("Network Switch", "SG-300", "Cisco"),
        ("Intercom System", "ITC-100", "Aiphone"),
        ("Motion Sensor", "MS-200", "Bosch"),
        ("Card Reader", "CR-500", "HID"),
    ]
    sites = db.query(Site).order_by(Site.id).all()
    for site in sites:
        for _ in range(random.randint(2, 3)):
            asset_name, model, manufacturer = random.choice(asset_types)
            asset_no = f"{manufacturer[:3].upper()}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            asset = Asset(
                company_id=site.company_id,
                site_id=site.id,
                asset_no=asset_no,
                name=asset_name,
                serial_no=f"SN-{random.randint(100000, 999999)}",
                model=model,
                manufacturer=manufacturer,
                installed_date=date.today() - timedelta(days=random.randint(0, 730)),
            )
            db.add(asset)
    db.commit()

    # ---- 8. Projects (10) ----
    project_statuses = ["Planning", "In Progress", "On Hold", "Complete"]
    project_names = [
        "Warehouse Security Upgrade",
        "Office Access Control Installation",
        "Fire Alarm Replacement",
        "CCTV Overhaul",
        "Retail Security System",
        "Data Centre Protection",
        "School Security Audit",
        "Construction Site Monitoring",
        "Hotel Access Modernisation",
        "Airport Perimeter Security",
    ]
    for company in companies:
        company_customers = [c for c in customers if c.company_id == company.id]
        company_sites = [s for s in sites if s.company_id == company.id]
        for _ in range(5):
            cust = random.choice(company_customers)
            site = random.choice(company_sites) if company_sites else None
            proj = Project(
                company_id=company.id,
                customer_id=cust.id,
                site_id=site.id if site else None,
                name=project_names.pop(0),
                status=random.choice(project_statuses),
                total=round(random.uniform(5000, 150000), 2),
            )
            db.add(proj)
    db.commit()

    # ---- 9. Jobs (16) ----
    job_statuses = ["Pending", "Approved", "In Progress", "Complete", "On Hold"]
    job_names = [
        "Install CCTV",
        "Upgrade Access",
        "Fire Panel Test",
        "Network Cabling",
        "Door Installation",
        "Alarm System",
        "Camera Maintenance",
        "Site Survey",
        "Electrical Work",
        "Security Audit",
        "System Integration",
        "Testing",
        "Repair",
        "Inspection",
        "Service Call",
        "Emergency Response",
    ]
    for company in companies:
        company_sites = [s for s in sites if s.company_id == company.id]
        for _ in range(8):
            site = random.choice(company_sites) if company_sites else None
            job = Job(
                company_id=company.id,
                name=job_names.pop(0),
                status=random.choice(job_statuses),
                date_issued=date.today() - timedelta(days=random.randint(0, 180)),
                total=round(random.uniform(500, 50000), 2),
            )
            db.add(job)
    db.commit()

    # ---- 10. Job Notes (32) ----
    note_subjects = [
        "Client Meeting",
        "Action Item",
        "Site Visit",
        "Report",
        "Follow-up",
    ]
    note_bodies = [
        "Confirmed stage 2 installation dates.",
        "Need additional power outlets.",
        "Customer requested extra sensors.",
        "Inspection passed.",
        "Parts ordered, ETA 2 weeks.",
        "Schedule conflict – reschedule.",
        "Update drawings accordingly.",
        "Final walkthrough completed.",
    ]
    jobs = db.query(Job).order_by(Job.id).all()
    employees = db.query(Employee).order_by(Employee.id).all()
    for job in jobs:
        for _ in range(2):
            note = JobNote(
                job_id=job.id,
                subject=random.choice(note_subjects),
                note=random.choice(note_bodies),
                date_created=seed_now - timedelta(days=random.randint(1, 90)),
                follow_up_date=(
                    (seed_now + timedelta(days=random.randint(1, 30))).date()
                    if random.random() < 0.5
                    else None
                ),
                visibility_admin=True,
                visibility_customer=random.random() < 0.3,
                reference_text=f"Job #{job.id}",
                reference_number=str(job.id),
                reference_type="Job",
                submitted_by_id=(
                    random.choice(employees).id if employees else None
                ),
                assign_to_id=(
                    random.choice(employees).id
                    if employees and random.random() < 0.5
                    else None
                ),
            )
            db.add(note)
    db.commit()

    # ---- 11. Attachments (20) ----
    file_names = [
        "site_plan.pdf",
        "wiring_diagram.pdf",
        "schedule.xlsx",
        "quote.pdf",
        "permit.pdf",
        "invoice.pdf",
        "specifications.pdf",
        "manual.pdf",
        "photo.jpg",
        "drawing.dwg",
        "compliance_report.pdf",
        "checklist.docx",
    ]
    mime_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "jpg": "image/jpeg",
        "dwg": "application/acad",
    }
    jobs = db.query(Job).order_by(Job.id).all()
    employees = db.query(Employee).order_by(Employee.id).all()
    # Attachment.ID is an opaque string upstream, not an autoincrementing
    # integer, so the seed assigns it explicitly. The counter keeps it
    # deterministic, and the "file-" prefix keeps it visibly non-numeric.
    file_counter = 0
    for job in jobs[:10]:  # attach to first 10 jobs
        for _ in range(random.randint(1, 3)):
            fname = random.choice(file_names)
            ext = fname.split(".")[-1]
            file_counter += 1
            attach = Attachment(
                id=f"file-{file_counter:04d}",
                job_id=job.id,
                filename=fname,
                mime_type=mime_types.get(ext, "application/octet-stream"),
                file_size_bytes=random.randint(50000, 5000000),
                date_added=seed_now - timedelta(days=random.randint(0, 60)),
                public=random.random() < 0.5,
                email=random.random() < 0.3,
                added_by_id=random.choice(employees).id if employees else None,
            )
            db.add(attach)
    db.commit()

    # ---- 12. Quotes (16) ----
    quote_statuses = ["Draft", "Sent", "Accepted", "Rejected"]
    quote_names = [
        "CCTV Quote",
        "Access Control Quote",
        "Fire Safety Quote",
        "Network Upgrade",
        "Security Package",
        "Maintenance Agreement",
        "Additional Sensors",
        "System Expansion",
        "Annual Service",
        "Emergency Callout",
        "Retrofit Proposal",
        "New Installation",
        "Consulting",
        "Training",
        "Support Plan",
        "Equipment Supply",
    ]
    for company in companies:
        company_customers = [c for c in customers if c.company_id == company.id]
        for _ in range(8):
            cust = random.choice(company_customers)
            quote = Quote(
                company_id=company.id,
                customer_id=cust.id,
                name=quote_names.pop(0),
                status=random.choice(quote_statuses),
                total=round(random.uniform(1000, 80000), 2),
            )
            db.add(quote)
    db.commit()

    db.close()
    print("✅ Seed data inserted successfully!")


if __name__ == "__main__":
    seed_data()
