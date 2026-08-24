from datetime import date

from sqlalchemy.orm import Session

from simpro_mock.database import SessionLocal
from simpro_mock.models import Company, Customer, Job, Quote


def seed_data():
    db: Session = SessionLocal()

    try:
        # Check if company already exists to prevent duplicate seeding
        if db.query(Company).filter(Company.id == 0).first():
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # 1. Create Company ID=0
        company = Company(
            id=0,
            name="CVC Test Company",
        )
        db.add(company)
        db.commit()

        # 2. Create Customers
        c1 = Customer(
            id=1,
            company_id=0,
            given_name="John",
            family_name="Smith",
            email="john.smith@example.com",
            phone="0412345678",
        )
        c2 = Customer(
            id=2,
            company_id=0,
            given_name="Jane",
            family_name="Doe",
            email="jane.doe@example.com",
            phone="0423456789",
        )
        c3 = Customer(
            id=3,
            company_id=0,
            given_name="Bob",
            family_name="Wilson",
            email="bob.wilson@example.com",
            phone="0434567890",
        )
        c4 = Customer(
            id=4,
            company_id=0,
            given_name="Alice",
            family_name="Brown",
            email="alice.brown@example.com",
            phone="07 3333 4444",
        )
        c5 = Customer(
            id=5,
            company_id=0,
            given_name="Charlie",
            family_name="Davis",
            email="charlie.davis@example.com",
            phone="07 5555 6666",
        )
        c6 = Customer(
            id=6,
            company_id=0,
            given_name="Diana",
            family_name="Evans",
            email="diana.evans@example.com",
            phone="07 7777 8888",
        )
        c7 = Customer(
            id=7,
            company_id=0,
            given_name="Edward",
            family_name="Foster",
            email="edward.foster@example.com",
            phone="07 9999 0000",
        )
        c8 = Customer(
            id=8,
            company_id=0,
            given_name="Fiona",
            family_name="Green",
            email="fiona.green@example.com",
            phone="07 2222 3333",
        )

        db.add_all([c1, c2, c3, c4, c5, c6, c7, c8])
        db.commit()

        # 3. Create Jobs
        j1 = Job(
            id=1,
            company_id=0,
            name="Kitchen Renovation",
            status="In Progress",
            date_issued=date(2026, 8, 20),
            total=15450.0,
        )
        j2 = Job(
            id=2,
            company_id=0,
            name="Bathroom Refit",
            status="Complete",
            date_issued=date(2026, 8, 15),
            total=8900.0,
        )
        j3 = Job(
            id=3,
            company_id=0,
            name="Office Fit-Out",
            status="Pending",
            date_issued=None,
            total=45000.0,
        )
        j4 = Job(
            id=4,
            company_id=0,
            name="Roof Repair",
            status="Pending",
            date_issued=date(2026, 8, 5),
            total=3500.00,
        )
        j5 = Job(
            id=5,
            company_id=0,
            name="Garage Conversion",
            status="Pending",
            date_issued=date(2026, 8, 10),
            total=18000.00,
        )
        j6 = Job(
            id=6,
            company_id=0,
            name="Garden Landscaping",
            status="Complete",
            date_issued=date(2026, 5, 20),
            total=7200.00,
        )
        j7 = Job(
            id=7,
            company_id=0,
            name="Driveway Paving",
            status="In Progress",
            date_issued=date(2026, 7, 28),
            total=5500.00,
        )
        j8 = Job(
            id=8,
            company_id=0,
            name="Loft Conversion",
            status="Pending",
            date_issued=date(2026, 8, 15),
            total=32000.00,
        )

        db.add_all([j1, j2, j3, j4, j5, j6, j7, j8])
        db.commit()

        # 4. Create Quotes
        q1 = Quote(
            id=1,
            company_id=0,
            customer_id=1,
            name="Kitchen Plastering",
            status="Approved",
            total=1200.0,
        )
        q2 = Quote(
            id=2,
            company_id=0,
            customer_id=2,
            name="Bathroom Tiling Quote",
            status="Pending",
            total=2450.0,
        )
        q3 = Quote(
            id=3,
            company_id=0,
            customer_id=3,
            name="Office Partitioning Estimate",
            status="Rejected",
            total=18000.0,
        )
        q4 = Quote(
            id=4,
            company_id=0,
            customer_id=4,
            name="Plumbing Overhaul",
            status="Draft",
            total=6800.00,
        )
        q5 = Quote(
            id=5,
            company_id=0,
            customer_id=5,
            name="Insulation Package",
            status="Sent",
            total=4200.00,
        )
        q6 = Quote(
            id=6,
            company_id=0,
            customer_id=6,
            name="Smart Home Wiring",
            status="Approved",
            total=11000.00,
        )
        q7 = Quote(
            id=7,
            company_id=0,
            customer_id=7,
            name="Deck Construction",
            status="Draft",
            total=8900.00,
        )
        q8 = Quote(
            id=8,
            company_id=0,
            customer_id=8,
            name="Window Replacement",
            status="Sent",
            total=17500.00,
        )

        db.add_all([q1, q2, q3, q4, q5, q6, q7, q8])
        db.commit()

        print("Database seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()