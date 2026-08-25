from datetime import date

from sqlalchemy.orm import Session

from simpro_mock.database import SessionLocal
from simpro_mock.models import Company, Customer, Job, Quote


def seed_data():
    db: Session = SessionLocal()

    try:
        # Check if all companies already exist
        if db.query(Company).filter(Company.id == 1).first() and db.query(Company).filter(Company.id == 2).first():
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # 1. Create Companies
        company1 = Company(
            id=1,
            name="CVC Service",
        )
        company2 = Company(
            id=2,
            name="CVC Projects",
        )

        db.add_all([company1, company2])
        db.commit()

        # -------------------------------------------------------------------
        # 2. Company 1 - CVC Service
        # -------------------------------------------------------------------

        # Customers
        c1 = Customer(
            id=1,
            company_id=1,
            given_name="John",
            family_name="Smith",
            email="john.smith@example.com",
            phone="0412345678",
        )
        c2 = Customer(
            id=2,
            company_id=1,
            given_name="Jane",
            family_name="Doe",
            email="jane.doe@example.com",
            phone="0423456789",
        )
        c3 = Customer(
            id=3,
            company_id=1,
            given_name="Bob",
            family_name="Wilson",
            email="bob.wilson@example.com",
            phone="0434567890",
        )
        c4 = Customer(
            id=4,
            company_id=1,
            given_name="Alice",
            family_name="Brown",
            email="alice.brown@example.com",
            phone="07 3333 4444",
        )
        c5 = Customer(
            id=5,
            company_id=1,
            given_name="Charlie",
            family_name="Davis",
            email="charlie.davis@example.com",
            phone="07 5555 6666",
        )
        c6 = Customer(
            id=6,
            company_id=1,
            given_name="Diana",
            family_name="Evans",
            email="diana.evans@example.com",
            phone="07 7777 8888",
        )
        c7 = Customer(
            id=7,
            company_id=1,
            given_name="Edward",
            family_name="Foster",
            email="edward.foster@example.com",
            phone="07 9999 0000",
        )
        c8 = Customer(
            id=8,
            company_id=1,
            given_name="Fiona",
            family_name="Green",
            email="fiona.green@example.com",
            phone="07 2222 3333",
        )
# Customers
        c9 = Customer(
            id=9,
            company_id=2,
            given_name="George",
            family_name="Harris",
            email="george.harris@example.com",
            phone="07 1111 2222",
        )
        c10 = Customer(
            id=10,
            company_id=2,
            given_name="Hannah",
            family_name="Irwin",
            email="hannah.irwin@example.com",
            phone="07 3344 5566",
        )
        c11 = Customer(
            id=11,
            company_id=2,
            given_name="Ian",
            family_name="Jacobs",
            email="ian.jacobs@example.com",
            phone="07 4455 6677",
        )
        c12 = Customer(
            id=12,
            company_id=2,
            given_name="Julia",
            family_name="Kim",
            email="julia.kim@example.com",
            phone="07 5566 7788",
        )
        c13 = Customer(
            id=13,
            company_id=2,
            given_name="Kevin",
            family_name="Lopez",
            email="kevin.lopez@example.com",
            phone="07 6677 8899",
        )
        c14 = Customer(
            id=14,
            company_id=2,
            given_name="Laura",
            family_name="Mitchell",
            email="laura.mitchell@example.com",
            phone="07 7788 9900",
        )
        c15 = Customer(
            id=15,
            company_id=2,
            given_name="Mark",
            family_name="Nolan",
            email="mark.nolan@example.com",
            phone="07 8899 0011",
        )
        c16 = Customer(
            id=16,
            company_id=2,
            given_name="Nora",
            family_name="Owens",
            email="nora.owens@example.com",
            phone="07 9900 1122",
        )       

        db.add_all([c1, c2, c3, c4, c5, c6, c7, c8,c9, c10, c11, c12, c13, c14, c15, c16])
        db.commit()

        # Jobs
        j1 = Job(
            id=1,
            company_id=1,
            name="Kitchen Renovation",
            status="In Progress",
            date_issued=date(2026, 8, 20),
            total=15450.0,
        )
        j2 = Job(
            id=2,
            company_id=1,
            name="Bathroom Refit",
            status="Complete",
            date_issued=date(2026, 8, 15),
            total=8900.0,
        )
        j3 = Job(
            id=3,
            company_id=1,
            name="Office Fit-Out",
            status="Pending",
            date_issued=None,
            total=45000.0,
        )
        j4 = Job(
            id=4,
            company_id=1,
            name="Roof Repair",
            status="Pending",
            date_issued=date(2026, 8, 5),
            total=3500.0,
        )
        j5 = Job(
            id=5,
            company_id=1,
            name="Garage Conversion",
            status="Pending",
            date_issued=date(2026, 8, 10),
            total=18000.0,
        )
        j6 = Job(
            id=6,
            company_id=1,
            name="Garden Landscaping",
            status="Complete",
            date_issued=date(2026, 5, 20),
            total=7200.0,
        )
        j7 = Job(
            id=7,
            company_id=1,
            name="Driveway Paving",
            status="In Progress",
            date_issued=date(2026, 7, 28),
            total=5500.0,
        )
        j8 = Job(
            id=8,
            company_id=1,
            name="Loft Conversion",
            status="Pending",
            date_issued=date(2026, 8, 15),
            total=32000.0,
        )
        j9 = Job(
                    id=9,
                    company_id=2,
                    name="Warehouse CCTV Install",
                    status="In Progress",
                    date_issued=date(2026, 8, 12),
                    total=84500.0,
                )
        j10 = Job(
                    id=10,
                    company_id=2,
                    name="Retail Chain Access Control",
                    status="Pending",
                    date_issued=None,
                    total=132000.0,
                )
        j11 = Job(
                    id=11,
                    company_id=2,
                    name="School Perimeter Security",
                    status="Complete",
                    date_issued=date(2026, 6, 1),
                    total=97250.0,
                )
        j12 = Job(
                    id=12,
                    company_id=2,
                    name="Data Centre Fire Suppression",
                    status="Pending",
                    date_issued=date(2026, 9, 1),
                    total=210000.0,
                )
        j13 = Job(
                    id=13,
                    company_id=2,
                    name="Hospital Wing Fit-Out",
                    status="In Progress",
                    date_issued=date(2026, 7, 15),
                    total=175600.0,
                )
        j14 = Job(
                    id=14,
                    company_id=2,
                    name="Logistics Hub Networking",
                    status="Complete",
                    date_issued=date(2026, 4, 30),
                    total=63000.0,
                )
        j15 = Job(
                    id=15,
                    company_id=2,
                    name="Stadium Public Address System",
                    status="Pending",
                    date_issued=date(2026, 8, 25),
                    total=148900.0,
                )
        j16 = Job(
                    id=16,
                    company_id=2,
                    name="Council Depot Upgrade",
                    status="In Progress",
                    date_issued=date(2026, 8, 1),
                    total=56750.0,
                )

        db.add_all([j1, j2, j3, j4, j5, j6, j7, j8,j9, j10, j11, j12, j13, j14, j15, j16])      
        db.commit()

        # Quotes
        q1 = Quote(
            id=1,
            company_id=1,
            customer_id=1,
            name="Kitchen Plastering",
            status="Approved",
            total=1200.0,
        )
        q2 = Quote(
            id=2,
            company_id=1,
            customer_id=2,
            name="Bathroom Tiling Quote",
            status="Pending",
            total=2450.0,
        )
        q3 = Quote(
            id=3,
            company_id=1,
            customer_id=3,
            name="Office Partitioning Estimate",
            status="Rejected",
            total=18000.0,
        )
        q4 = Quote(
            id=4,
            company_id=1,
            customer_id=4,
            name="Plumbing Overhaul",
            status="Draft",
            total=6800.0,
        )
        q5 = Quote(
            id=5,
            company_id=1,
            customer_id=5,
            name="Insulation Package",
            status="Sent",
            total=4200.0,
        )
        q6 = Quote(
            id=6,
            company_id=1,
            customer_id=6,
            name="Smart Home Wiring",
            status="Approved",
            total=11000.0,
        )
        q7 = Quote(
            id=7,
            company_id=1,
            customer_id=7,
            name="Deck Construction",
            status="Draft",
            total=8900.0,
        )
        q8 = Quote(
            id=8,
            company_id=1,
            customer_id=8,
            name="Window Replacement",
            status="Sent",
            total=17500.0,
        )
        q9 = Quote(
                    id=9,
                    company_id=2,
                    customer_id=9,
                    name="CCTV Camera Package (48 units)",
                    status="Approved",
                    total=42000.0,
                )
        q10 = Quote(
                    id=10,
                    company_id=2,
                    customer_id=10,
                    name="Access Control Estimate",
                    status="Sent",
                    total=28500.0,
                )
        q11 = Quote(
                    id=11,
                    company_id=2,
                    customer_id=11,
                    name="Perimeter Fencing & Sensors",
                    status="Approved",
                    total=51200.0,
                )
        q12 = Quote(
                    id=12,
                    company_id=2,
                    customer_id=12,
                    name="Fire Suppression Design",
                    status="Draft",
                    total=76000.0,
                )
        q13 = Quote(
                    id=13,
                    company_id=2,
                    customer_id=13,
                    name="Ward Wiring & Nurse Call System",
                    status="Pending",
                    total=39900.0,
                )
        q14 = Quote(
                    id=14,
                    company_id=2,
                    customer_id=14,
                    name="Warehouse Network Cabling",
                    status="Rejected",
                    total=22750.0,
                )
        q15 = Quote(
                    id=15,
                    company_id=2,
                    customer_id=15,
                    name="PA System Install Estimate",
                    status="Sent",
                    total=61300.0,
                )
        q16 = Quote(
                    id=16,
                    company_id=2,
                    customer_id=16,
                    name="Depot CCTV Upgrade Quote",
                    status="Approved",
                    total=33400.0,
                )

        db.add_all([q1, q2, q3, q4, q5, q6, q7, q8,q9, q10, q11, q12, q13, q14, q15, q16])
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