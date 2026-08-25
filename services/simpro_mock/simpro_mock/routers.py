from fastapi import APIRouter, Depends, Form, HTTPException, Query, Response
from sqlalchemy.orm import Session
from starlette.requests import Request

from simpro_mock.config import settings
from simpro_mock.database import get_db
from simpro_mock.filtering import apply_filters
from simpro_mock.middleware import paginate_query, set_pagination_headers
from simpro_mock.models import Company, Customer, Job, Quote
from simpro_mock.schemas import (
    CompanyResponse,
    CustomerResponse,
    HealthResponse,
    JobResponse,
    QuoteResponse,
    TokenResponse,
)

# Create separate routers for health, tokens, and API resources
health_router = APIRouter()
token_router = APIRouter()
api_router = APIRouter(prefix="/api/v1.0")


# ==========================================
# 1. HEALTH CHECK & INFRASTRUCTURE ROUTES
# ==========================================

@health_router.get("/health", response_model=HealthResponse)
def health_check():
    """Verify that the FastAPI service is active and responsive."""
    return HealthResponse(
        status="ok",
        service="simpro-mock",
        version="0.1.0",
    )


@token_router.post("/oauth2/token", response_model=TokenResponse)
def issue_token(
    grant_type: str = Form("client_credentials"),
    client_id: str = Form(""),
    client_secret: str = Form(""),
):
    """
    Accept form-encoded OAuth2 client credentials and return a static mock access token.
    This simulates standard authorization scopes and response properties of Simpro.
    """
    return TokenResponse(
        access_token=settings.mock_access_token,
        token_type="Bearer",
        expires_in=settings.token_expires_in,
    )


# ==========================================
# 2. COMPANIES RESOURCE ROUTES
# ==========================================

@api_router.get("/companies/", response_model=list[CompanyResponse])
def list_companies(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    db: Session = Depends(get_db),
):
    """Retrieve all seeded company entities with filtering and pagination."""
    query = db.query(Company)
    query = apply_filters(query, Company, dict(request.query_params))

    items, total, total_pages = paginate_query(query, page, pageSize)

    results = [
        CompanyResponse(
            ID=company.id,
            Name=company.name,
        )
        for company in items
    ]

    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    """Fetch a single company by its unique identifier."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return CompanyResponse(
        ID=company.id,
        Name=company.name,
    )


# ==========================================
# 3. CUSTOMERS RESOURCE ROUTES
# ==========================================

@api_router.get(
    "/companies/{company_id}/customers/",
    response_model=list[CustomerResponse],
)
def list_customers(
    company_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    db: Session = Depends(get_db),
):
    """Retrieve all customers scoped to a company ID with filtering and pagination."""
    query = db.query(Customer).filter(Customer.company_id == company_id)
    query = apply_filters(query, Customer, dict(request.query_params))

    items, total, total_pages = paginate_query(query, page, pageSize)

    results = [
        CustomerResponse(
            ID=customer.id,
            CompanyID=customer.company_id,
            GivenName=customer.given_name,
            FamilyName=customer.family_name,
            Email=customer.email,
            Phone=customer.phone,
        )
        for customer in items
    ]

    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get(
    "/companies/{company_id}/customers/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    company_id: int,
    customer_id: int,
    db: Session = Depends(get_db),
):
    """Fetch details of a single customer scoped to their respective company."""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.company_id == company_id,
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return CustomerResponse(
        ID=customer.id,
        CompanyID=customer.company_id,
        GivenName=customer.given_name,
        FamilyName=customer.family_name,
        Email=customer.email,
        Phone=customer.phone,
    )


# ==========================================
# 4. JOBS RESOURCE ROUTES
# ==========================================

@api_router.get(
    "/companies/{company_id}/jobs/",
    response_model=list[JobResponse],
)
def list_jobs(
    company_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    db: Session = Depends(get_db),
):
    """Retrieve all jobs scoped to a company with filtering and pagination."""
    query = db.query(Job).filter(Job.company_id == company_id)
    query = apply_filters(query, Job, dict(request.query_params))

    items, total, total_pages = paginate_query(query, page, pageSize)

    results = [
        JobResponse(
            ID=job.id,
            CompanyID=job.company_id,
            Name=job.name,
            Status=job.status,
            DateIssued=(
                job.date_issued.isoformat()
                if job.date_issued
                else None
            ),
            Total=job.total,
        )
        for job in items
    ]

    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get(
    "/companies/{company_id}/jobs/{job_id}",
    response_model=JobResponse,
)
def get_job(
    company_id: int,
    job_id: int,
    db: Session = Depends(get_db),
):
    """Fetch details of a single job scoped to a specific company ID."""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.company_id == company_id,
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        ID=job.id,
        CompanyID=job.company_id,
        Name=job.name,
        Status=job.status,
        DateIssued=job.date_issued.isoformat() if job.date_issued else None,
        Total=job.total,
    )


# ==========================================
# 5. QUOTES RESOURCE ROUTES
# ==========================================

@api_router.get(
    "/companies/{company_id}/quotes/",
    response_model=list[QuoteResponse],
)
def list_quotes(
    company_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    db: Session = Depends(get_db),
):
    """Retrieve all quotes scoped to a company with filtering and pagination."""
    query = db.query(Quote).filter(Quote.company_id == company_id)
    query = apply_filters(query, Quote, dict(request.query_params))

    items, total, total_pages = paginate_query(query, page, pageSize)

    results = [
        QuoteResponse(
            ID=quote.id,
            CompanyID=quote.company_id,
            CustomerID=quote.customer_id,
            Name=quote.name,
            Status=quote.status,
            Total=quote.total,
        )
        for quote in items
    ]

    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get(
    "/companies/{company_id}/quotes/{quote_id}",
    response_model=QuoteResponse,
)
def get_quote(
    company_id: int,
    quote_id: int,
    db: Session = Depends(get_db),
):
    """Fetch details of a single quote scoped to a specific company ID."""
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.company_id == company_id,
    ).first()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    return QuoteResponse(
        ID=quote.id,
        CompanyID=quote.company_id,
        CustomerID=quote.customer_id,
        Name=quote.name,
        Status=quote.status,
        Total=quote.total,
    )