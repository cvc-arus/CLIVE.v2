from fastapi import APIRouter, Depends, Form, HTTPException, Query, Response
from sqlalchemy.orm import Session
from starlette.requests import Request

from simpro_mock.config import settings
from simpro_mock.database import get_db
from simpro_mock.filtering import apply_filters
from simpro_mock.middleware import paginate_query, set_pagination_headers
from simpro_mock.models import (
    Asset,
    Attachment,
    Company,
    Contact,
    Customer,
    Employee,
    Job,
    JobNote,
    Quote,
    Site,
    Status,
)
from simpro_mock.schemas import (
    AssetResponse,
    AttachmentDetailResponse,
    AttachmentListResponse,
    CompanyDetailResponse,
    CompanyListResponse,
    ContactResponse,
    CustomerResponse,
    EmployeeDetailResponse,
    EmployeeListResponse,
    HealthResponse,
    JobNoteDetailResponse,
    JobNoteListResponse,
    JobResponse,
    ProjectStatusCodeDetailResponse,
    ProjectStatusCodeListResponse,
    QuoteResponse,
    SiteResponse,
    TokenResponse,
)
from simpro_mock.serializers import (
    attachment_detail_dict,
    attachment_list_dict,
    company_detail_dict,
    company_list_dict,
    employee_detail_dict,
    employee_list_dict,
    job_note_detail_dict,
    job_note_list_dict,
    project_status_code_detail_dict,
    project_status_code_list_dict,
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


@api_router.get("/companies/", response_model=list[CompanyListResponse])
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

    results = [company_list_dict(company) for company in items]

    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get("/companies/{company_id}", response_model=CompanyDetailResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    """Fetch a single company by its unique identifier."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return company_detail_dict(company)


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
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.company_id == company_id,
        )
        .first()
    )

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
            DateIssued=(job.date_issued.isoformat() if job.date_issued else None),
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
    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.company_id == company_id,
        )
        .first()
    )

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
    quote = (
        db.query(Quote)
        .filter(
            Quote.id == quote_id,
            Quote.company_id == company_id,
        )
        .first()
    )

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


@api_router.get(
    "/companies/{company_id}/customers/{customer_id}/contacts/",
    response_model=list[ContactResponse],
)
def list_contacts(
    company_id: int,
    customer_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    db: Session = Depends(get_db),
):
    query = db.query(Contact).filter(
        Contact.company_id == company_id, Contact.customer_id == customer_id
    )
    query = apply_filters(query, Contact, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [
        ContactResponse(
            ID=c.id,
            CompanyID=c.company_id,
            CustomerID=c.customer_id,
            GivenName=c.given_name,
            FamilyName=c.family_name,
            Position=c.position,
            Email=c.email,
            Phone=c.phone,
        )
        for c in items
    ]
    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get(
    "/companies/{company_id}/customers/{customer_id}/contacts/{contact_id}",
    response_model=ContactResponse,
)
def get_contact(
    company_id: int, customer_id: int, contact_id: int, db: Session = Depends(get_db)
):
    contact = (
        db.query(Contact)
        .filter(
            Contact.id == contact_id,
            Contact.company_id == company_id,
            Contact.customer_id == customer_id,
        )
        .first()
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactResponse(
        ID=contact.id,
        CompanyID=contact.company_id,
        CustomerID=contact.customer_id,
        GivenName=contact.given_name,
        FamilyName=contact.family_name,
        Position=contact.position,
        Email=contact.email,
        Phone=contact.phone,
    )


# ==========================================
# 7. SITES
# ==========================================


@api_router.get("/companies/{company_id}/sites/", response_model=list[SiteResponse])
def list_sites(
    company_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    db: Session = Depends(get_db),
):
    query = db.query(Site).filter(Site.company_id == company_id)
    query = apply_filters(query, Site, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [
        SiteResponse(
            ID=s.id,
            CompanyID=s.company_id,
            CustomerID=s.customer_id,
            Name=s.name,
            Address=s.address,
            City=s.city,
            Postcode=s.postcode,
            State=s.state,
            Country=s.country,
        )
        for s in items
    ]
    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get("/companies/{company_id}/sites/{site_id}", response_model=SiteResponse)
def get_site(company_id: int, site_id: int, db: Session = Depends(get_db)):
    site = (
        db.query(Site).filter(Site.id == site_id, Site.company_id == company_id).first()
    )
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return SiteResponse(
        ID=site.id,
        CompanyID=site.company_id,
        CustomerID=site.customer_id,
        Name=site.name,
        Address=site.address,
        City=site.city,
        Postcode=site.postcode,
        State=site.state,
        Country=site.country,
    )


# ==========================================
# 8. ASSETS
# ==========================================


@api_router.get(
    "/companies/{company_id}/sites/{site_id}/assets/",
    response_model=list[AssetResponse],
)
def list_assets(
    company_id: int,
    site_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    db: Session = Depends(get_db),
):
    query = db.query(Asset).filter(
        Asset.company_id == company_id, Asset.site_id == site_id
    )
    query = apply_filters(query, Asset, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [
        AssetResponse(
            ID=a.id,
            CompanyID=a.company_id,
            SiteID=a.site_id,
            AssetNo=a.asset_no,
            Name=a.name,
            SerialNo=a.serial_no,
            Model=a.model,
            Manufacturer=a.manufacturer,
            InstalledDate=a.installed_date.isoformat() if a.installed_date else None,
        )
        for a in items
    ]
    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get(
    "/companies/{company_id}/sites/{site_id}/assets/{asset_id}",
    response_model=AssetResponse,
)
def get_asset(
    company_id: int, site_id: int, asset_id: int, db: Session = Depends(get_db)
):
    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id,
            Asset.company_id == company_id,
            Asset.site_id == site_id,
        )
        .first()
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetResponse(
        ID=asset.id,
        CompanyID=asset.company_id,
        SiteID=asset.site_id,
        AssetNo=asset.asset_no,
        Name=asset.name,
        SerialNo=asset.serial_no,
        Model=asset.model,
        Manufacturer=asset.manufacturer,
        InstalledDate=asset.installed_date.isoformat()
        if asset.installed_date
        else None,
    )


# ==========================================
# 9. EMPLOYEES
# ==========================================


@api_router.get(
    "/companies/{company_id}/employees/", response_model=list[EmployeeListResponse]
)
def list_employees(
    company_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    db: Session = Depends(get_db),
):
    query = db.query(Employee).filter(Employee.company_id == company_id)
    query = apply_filters(query, Employee, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [employee_list_dict(e) for e in items]
    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get(
    "/companies/{company_id}/employees/{employee_id}",
    response_model=EmployeeDetailResponse,
)
def get_employee(company_id: int, employee_id: int, db: Session = Depends(get_db)):
    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id, Employee.company_id == company_id)
        .first()
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee_detail_dict(employee)


# ==========================================
# 10. JOB NOTES
# ==========================================


@api_router.get(
    "/companies/{company_id}/jobs/{job_id}/notes/",
    response_model=list[JobNoteListResponse],
)
def list_job_notes(
    company_id: int,
    job_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    db: Session = Depends(get_db),
):
    # Optional: verify that the job belongs to the company
    job = db.query(Job).filter(Job.id == job_id, Job.company_id == company_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    query = db.query(JobNote).filter(JobNote.job_id == job_id)
    query = apply_filters(query, JobNote, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [job_note_list_dict(n) for n in items]
    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get(
    "/companies/{company_id}/jobs/{job_id}/notes/{note_id}",
    response_model=JobNoteDetailResponse,
)
def get_job_note(
    company_id: int, job_id: int, note_id: int, db: Session = Depends(get_db)
):
    note = (
        db.query(JobNote)
        .filter(JobNote.id == note_id, JobNote.job_id == job_id)
        .first()
    )
    # Verify job belongs to company (optional)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    job = db.query(Job).filter(Job.id == job_id, Job.company_id == company_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_note_detail_dict(note)


# ==========================================
# 11. ATTACHMENTS
# ==========================================


@api_router.get(
    "/companies/{company_id}/jobs/{job_id}/attachments/files/",
    response_model=list[AttachmentListResponse],
)
def list_attachments(
    company_id: int,
    job_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id, Job.company_id == company_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    query = db.query(Attachment).filter(Attachment.job_id == job_id)
    query = apply_filters(query, Attachment, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [attachment_list_dict(a) for a in items]
    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get(
    "/companies/{company_id}/jobs/{job_id}/attachments/files/{file_id}",
    response_model=AttachmentDetailResponse,
)
def get_attachment(
    company_id: int, job_id: int, file_id: str, db: Session = Depends(get_db)
):
    attachment = (
        db.query(Attachment)
        .filter(Attachment.id == file_id, Attachment.job_id == job_id)
        .first()
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    job = db.query(Job).filter(Job.id == job_id, Job.company_id == company_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return attachment_detail_dict(attachment)


# ==========================================
# 12. PROJECT STATUS CODES
# ==========================================


@api_router.get(
    "/companies/{company_id}/setup/statusCodes/projects/",
    response_model=list[ProjectStatusCodeListResponse],
)
def list_project_status_codes(
    company_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    db: Session = Depends(get_db),
):
    query = db.query(Status).filter(Status.company_id == company_id)
    query = apply_filters(query, Status, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [project_status_code_list_dict(s) for s in items]
    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get(
    "/companies/{company_id}/setup/statusCodes/projects/{status_code_id}",
    response_model=ProjectStatusCodeDetailResponse,
)
def get_project_status_code(
    company_id: int, status_code_id: int, db: Session = Depends(get_db)
):
    status = (
        db.query(Status)
        .filter(Status.id == status_code_id, Status.company_id == company_id)
        .first()
    )
    if not status:
        raise HTTPException(status_code=404, detail="Project status code not found")
    return project_status_code_detail_dict(status)
