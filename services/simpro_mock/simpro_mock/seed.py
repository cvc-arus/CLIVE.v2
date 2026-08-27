# simpro_mock/seed.py

import random
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from simpro_mock.models import (
    Company, Customer, Contact, Site, Asset, Employee, Project,
    Job, JobNote, Attachment, Quote, Status
)
from simpro_mock.database import SessionLocal


def truncate_tables(db: Session):
    """Truncate all tables and reset identity sequences."""
    # Order doesn't matter much with CASCADE, but we list all tables explicitly.
    tables = [
        "attachments", "job_notes", "projects", "assets",
        "statuses", "employees", "sites", "contacts",
        "quotes", "jobs", "customers", "companies"
    ]
    for table in tables:
        db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
    db.commit()
    print("✅ All tables truncated.")


def get_or_create_company(db: Session, name: str) -> Company:
    company = db.query(Company).filter(Company.name == name).first()
    if not company:
        company = Company(name=name)
        db.add(company)
        db.flush()
    return company


def seed_data():
    db = SessionLocal()

    # --- Clear existing data ---
    truncate_tables(db)

    # ---- 1. Companies ----
    companies = [
        get_or_create_company(db, "CVC Service"),
        get_or_create_company(db, "CVC Projects"),
    ]
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
    customers = []
    for company in companies:
        for _ in range(8):  # 8 per company = total 16
            first, last, email, phone = customer_data.pop(0)
            cust = Customer(
                company_id=company.id,
                given_name=first,
                family_name=last,
                email=email,
                phone=phone,
            )
            db.add(cust)
            customers.append(cust)
    db.commit()

    # ---- 3. Contacts (24) ----
    positions = ["Site Manager", "Accounts Contact", "Facilities Manager", "Operations Manager", "Project Coordinator"]
    for customer in customers:
        for pos in random.sample(positions, k=3):
            contact = Contact(
                company_id=customer.company_id,
                customer_id=customer.id,
                given_name=f"Contact_{pos.replace(' ', '_')}_{customer.id}",
                family_name=customer.family_name,
                position=pos,
                email=f"{pos.replace(' ', '.')}.{customer.family_name}@example.com",
                phone=f"04{random.randint(10000000, 99999999)}",
            )
            db.add(contact)
    db.commit()

    # ---- 4. Sites (16) ----
    site_names = [
        "Smith Residence", "Doe Office", "Johnson Warehouse", "Williams Retail",
        "Brown Factory", "Green Depot", "Miller Medical", "Taylor School",
        "Harris Estate", "Owens Tower", "Nelson Complex", "Carter Plaza",
        "Parker Centre", "Cooper Court", "Reed Gardens", "Bennett House",
    ]
    cities = ["Brisbane", "Sydney", "Melbourne", "Perth", "Adelaide"]
    states = ["QLD", "NSW", "VIC", "WA", "SA"]
    for company in companies:
        company_customers = [c for c in customers if c.company_id == company.id]
        for _ in range(8):
            cust = random.choice(company_customers)
            site = Site(
                company_id=company.id,
                customer_id=cust.id,
                name=site_names.pop(0),
                address=f"{random.randint(1, 999)} {random.choice(['Main', 'Park', 'Queen', 'George', 'Albert'])} {random.choice(['St', 'Ave', 'Rd', 'Blvd'])}",
                city=random.choice(cities),
                postcode=f"{random.randint(2000, 7000)}",
                state=random.choice(states),
                country="Australia",
            )
            db.add(site)
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
        for emp in employee_data[:6]:  # 6 per company = total 12
            given, family, pos = emp
            employee = Employee(
                company_id=company.id,
                given_name=given,
                family_name=family,
                position=pos,
                email=f"{given.lower()}.{family.lower()}@cvc.com.au",
                phone=f"04{random.randint(10000000, 99999999)}",
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
    for company in companies:
        for name, category in status_names:
            status = Status(
                company_id=company.id,
                name=name,
                category=category,
                is_default=1 if name == "Pending" else 0,
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
    sites = db.query(Site).all()
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
        "Install CCTV", "Upgrade Access", "Fire Panel Test", "Network Cabling",
        "Door Installation", "Alarm System", "Camera Maintenance", "Site Survey",
        "Electrical Work", "Security Audit", "System Integration", "Testing",
        "Repair", "Inspection", "Service Call", "Emergency Response",
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
    note_subjects = ["Client Meeting", "Action Item", "Site Visit", "Report", "Follow-up"]
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
    jobs = db.query(Job).all()
    employees = db.query(Employee).all()
    for job in jobs:
        for _ in range(2):
            note = JobNote(
                job_id=job.id,
                subject=random.choice(note_subjects),
                note=random.choice(note_bodies),
                created_by=random.choice(employees).id if employees else None,
                created_at=datetime.now() - timedelta(days=random.randint(1, 90)),
            )
            db.add(note)
    db.commit()

    # ---- 11. Attachments (20) ----
    file_names = [
        "site_plan.pdf", "wiring_diagram.pdf", "schedule.xlsx", "quote.pdf",
        "permit.pdf", "invoice.pdf", "specifications.pdf", "manual.pdf",
        "photo.jpg", "drawing.dwg", "compliance_report.pdf", "checklist.docx",
    ]
    mime_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "jpg": "image/jpeg",
        "dwg": "application/acad",
    }
    jobs = db.query(Job).all()
    for job in jobs[:10]:  # attach to first 10 jobs
        for _ in range(random.randint(1, 3)):
            fname = random.choice(file_names)
            ext = fname.split('.')[-1]
            attach = Attachment(
                job_id=job.id,
                filename=fname,
                mime_type=mime_types.get(ext, "application/octet-stream"),
                file_size=random.randint(50000, 5000000),
                uploaded_at=datetime.now() - timedelta(days=random.randint(0, 60)),
            )
            db.add(attach)
    db.commit()

    # ---- 12. Quotes (16) ----
    quote_statuses = ["Draft", "Sent", "Accepted", "Rejected"]
    quote_names = [
        "CCTV Quote", "Access Control Quote", "Fire Safety Quote",
        "Network Upgrade", "Security Package", "Maintenance Agreement",
        "Additional Sensors", "System Expansion", "Annual Service",
        "Emergency Callout", "Retrofit Proposal", "New Installation",
        "Consulting", "Training", "Support Plan", "Equipment Supply",
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