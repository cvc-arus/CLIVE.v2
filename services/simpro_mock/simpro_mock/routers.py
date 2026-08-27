from fastapi import APIRouter, Depends, Form, HTTPException, Query, Response
from sqlalchemy.orm import Session
from starlette.requests import Request

from simpro_mock.config import settings
from simpro_mock.database import get_db
from simpro_mock.filtering import apply_filters
from simpro_mock.middleware import paginate_query, set_pagination_headers
from simpro_mock.models import Contact, Site, Asset, Employee, Project, JobNote, Attachment, Status, Company, Customer, Job, Quote
from simpro_mock.schemas import (
    ContactResponse,
    SiteResponse,
    AssetResponse,
    EmployeeResponse,
    ProjectResponse,
    JobNoteResponse,
    AttachmentResponse,
    StatusResponse,
    HealthResponse,
    TokenResponse,
    CompanyResponse,
    CustomerResponse,
    JobResponse,
    QuoteResponse,
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

@api_router.get("/companies/{company_id}/customers/{customer_id}/contacts/", response_model=list[ContactResponse])
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
        Contact.company_id == company_id,
        Contact.customer_id == customer_id
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


@api_router.get("/companies/{company_id}/customers/{customer_id}/contacts/{contact_id}", response_model=ContactResponse)
def get_contact(company_id: int, customer_id: int, contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.company_id == company_id,
        Contact.customer_id == customer_id
    ).first()
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
    site = db.query(Site).filter(Site.id == site_id, Site.company_id == company_id).first()
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

@api_router.get("/companies/{company_id}/sites/{site_id}/assets/", response_model=list[AssetResponse])
def list_assets(
    company_id: int,
    site_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    db: Session = Depends(get_db),
):
    query = db.query(Asset).filter(Asset.company_id == company_id, Asset.site_id == site_id)
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


@api_router.get("/companies/{company_id}/sites/{site_id}/assets/{asset_id}", response_model=AssetResponse)
def get_asset(company_id: int, site_id: int, asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.company_id == company_id,
        Asset.site_id == site_id
    ).first()
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
        InstalledDate=asset.installed_date.isoformat() if asset.installed_date else None,
    )


# ==========================================
# 9. EMPLOYEES
# ==========================================

@api_router.get("/companies/{company_id}/employees/", response_model=list[EmployeeResponse])
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
    results = [
        EmployeeResponse(
            ID=e.id,
            CompanyID=e.company_id,
            GivenName=e.given_name,
            FamilyName=e.family_name,
            Position=e.position,
            Email=e.email,
            Phone=e.phone,
        )
        for e in items
    ]
    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get("/companies/{company_id}/employees/{employee_id}", response_model=EmployeeResponse)
def get_employee(company_id: int, employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id, Employee.company_id == company_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return EmployeeResponse(
        ID=employee.id,
        CompanyID=employee.company_id,
        GivenName=employee.given_name,
        FamilyName=employee.family_name,
        Position=employee.position,
        Email=employee.email,
        Phone=employee.phone,
    )


# ==========================================
# 10. PROJECTS
# ==========================================

@api_router.get("/companies/{company_id}/projects/", response_model=list[ProjectResponse])
def list_projects(
    company_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    db: Session = Depends(get_db),
):
    query = db.query(Project).filter(Project.company_id == company_id)
    query = apply_filters(query, Project, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [
        ProjectResponse(
            ID=p.id,
            CompanyID=p.company_id,
            CustomerID=p.customer_id,
            SiteID=p.site_id,
            Name=p.name,
            Status=p.status,
            Total=p.total,
        )
        for p in items
    ]
    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get("/companies/{company_id}/projects/{project_id}", response_model=ProjectResponse)
def get_project(company_id: int, project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id, Project.company_id == company_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        ID=project.id,
        CompanyID=project.company_id,
        CustomerID=project.customer_id,
        SiteID=project.site_id,
        Name=project.name,
        Status=project.status,
        Total=project.total,
    )


# ==========================================
# 11. JOB NOTES
# ==========================================

@api_router.get("/companies/{company_id}/jobs/{job_id}/notes/", response_model=list[JobNoteResponse])
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
    results = [
        JobNoteResponse(
            ID=n.id,
            JobID=n.job_id,
            Subject=n.subject,
            Note=n.note,
            CreatedBy=n.created_by,
            CreatedAt=n.created_at.isoformat() if n.created_at else None,
        )
        for n in items
    ]
    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get("/companies/{company_id}/jobs/{job_id}/notes/{note_id}", response_model=JobNoteResponse)
def get_job_note(company_id: int, job_id: int, note_id: int, db: Session = Depends(get_db)):
    note = db.query(JobNote).filter(
        JobNote.id == note_id,
        JobNote.job_id == job_id
    ).first()
    # Verify job belongs to company (optional)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    job = db.query(Job).filter(Job.id == job_id, Job.company_id == company_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobNoteResponse(
        ID=note.id,
        JobID=note.job_id,
        Subject=note.subject,
        Note=note.note,
        CreatedBy=note.created_by,
        CreatedAt=note.created_at.isoformat() if note.created_at else None,
    )


# ==========================================
# 12. ATTACHMENTS
# ==========================================

@api_router.get("/companies/{company_id}/jobs/{job_id}/attachments/", response_model=list[AttachmentResponse])
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
    results = [
        AttachmentResponse(
            ID=a.id,
            JobID=a.job_id,
            Filename=a.filename,
            MimeType=a.mime_type,
            FileSize=a.file_size,
            UploadedAt=a.uploaded_at.isoformat() if a.uploaded_at else None,
        )
        for a in items
    ]
    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get("/companies/{company_id}/jobs/{job_id}/attachments/{attachment_id}", response_model=AttachmentResponse)
def get_attachment(company_id: int, job_id: int, attachment_id: int, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id,
        Attachment.job_id == job_id
    ).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    job = db.query(Job).filter(Job.id == job_id, Job.company_id == company_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return AttachmentResponse(
        ID=attachment.id,
        JobID=attachment.job_id,
        Filename=attachment.filename,
        MimeType=attachment.mime_type,
        FileSize=attachment.file_size,
        UploadedAt=attachment.uploaded_at.isoformat() if attachment.uploaded_at else None,
    )


# ==========================================
# 13. STATUSES
# ==========================================

@api_router.get("/companies/{company_id}/statuses/", response_model=list[StatusResponse])
def list_statuses(
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
    results = [
        StatusResponse(
            ID=s.id,
            CompanyID=s.company_id,
            Name=s.name,
            Category=s.category,
            IsDefault=bool(s.is_default),
        )
        for s in items
    ]
    set_pagination_headers(response, total, len(results), total_pages)
    return results


@api_router.get("/companies/{company_id}/statuses/{status_id}", response_model=StatusResponse)
def get_status(company_id: int, status_id: int, db: Session = Depends(get_db)):
    status = db.query(Status).filter(Status.id == status_id, Status.company_id == company_id).first()
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    return StatusResponse(
        ID=status.id,
        CompanyID=status.company_id,
        Name=status.name,
        Category=status.category,
        IsDefault=bool(status.is_default),
    )