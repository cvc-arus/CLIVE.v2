from fastapi import APIRouter, Depends, Form, HTTPException, Query, Response
from sqlalchemy.orm import Session
from starlette.requests import Request

from simpro_mock.config import settings
from simpro_mock.database import get_db
from simpro_mock.filtering import apply_filters
from simpro_mock.middleware import paginate_query
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
from simpro_mock.projection import collection_response, detail_response
from simpro_mock.schemas import (
    AssetDetailResponse,
    AssetListResponse,
    AttachmentDetailResponse,
    AttachmentListResponse,
    CompanyCustomerDetailResponse,
    CompanyCustomerListResponse,
    CompanyDetailResponse,
    CompanyListResponse,
    ContactDetailResponse,
    ContactListResponse,
    CustomerSummaryResponse,
    EmployeeDetailResponse,
    EmployeeListResponse,
    HealthResponse,
    IndividualCustomerDetailResponse,
    IndividualCustomerListResponse,
    JobDetailResponse,
    JobListResponse,
    JobNoteDetailResponse,
    JobNoteListResponse,
    ProjectStatusCodeDetailResponse,
    ProjectStatusCodeListResponse,
    QuoteDetailResponse,
    QuoteListResponse,
    SiteDetailResponse,
    SiteListResponse,
    TokenResponse,
)
from simpro_mock.serializers import (
    asset_detail_dict,
    asset_list_dict,
    attachment_detail_dict,
    attachment_list_dict,
    company_customer_detail_dict,
    company_customer_list_dict,
    company_detail_dict,
    company_list_dict,
    contact_detail_dict,
    contact_list_dict,
    customer_summary_dict,
    employee_detail_dict,
    employee_list_dict,
    individual_customer_detail_dict,
    individual_customer_list_dict,
    job_detail_dict,
    job_list_dict,
    job_note_detail_dict,
    job_note_list_dict,
    project_status_code_detail_dict,
    project_status_code_list_dict,
    quote_detail_dict,
    quote_list_dict,
    site_detail_dict,
    site_list_dict,
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
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Retrieve all seeded company entities with filtering and pagination."""
    query = db.query(Company)
    query = apply_filters(query, Company, dict(request.query_params))

    items, total, total_pages = paginate_query(query, page, pageSize)

    results = [company_list_dict(company) for company in items]

    return collection_response(response, results, total, total_pages, columns)


@api_router.get("/companies/{company_id}", response_model=CompanyDetailResponse)
def get_company(
    company_id: int, columns: str | None = Query(None), db: Session = Depends(get_db)
):
    """Fetch a single company by its unique identifier."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return detail_response(company_detail_dict(company), columns)


# ==========================================
# 3. CUSTOMERS RESOURCE ROUTES
#
# Three routes, not two: /customers/ lists both kinds with a Type
# discriminator and an _href, and the full record lives on a subtype route.
# Simpro publishes no /customers/{id}. See ADR-013 decision 2.
# ==========================================


@api_router.get(
    "/companies/{company_id}/customers/",
    response_model=list[CustomerSummaryResponse],
)
def list_customers(
    company_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List both customer kinds together, with the Type discriminator."""
    query = db.query(Customer).filter(Customer.company_id == company_id)
    query = apply_filters(query, Customer, dict(request.query_params))

    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [customer_summary_dict(customer) for customer in items]

    return collection_response(response, results, total, total_pages, columns)


@api_router.get(
    "/companies/{company_id}/customers/individuals/",
    response_model=list[IndividualCustomerListResponse],
)
def list_individual_customers(
    company_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List only the customers who are people."""
    query = db.query(Customer).filter(
        Customer.company_id == company_id, Customer.type == "Individual"
    )
    query = apply_filters(query, Customer, dict(request.query_params))

    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [individual_customer_list_dict(customer) for customer in items]

    return collection_response(response, results, total, total_pages, columns)


@api_router.get(
    "/companies/{company_id}/customers/individuals/{customer_id}",
    response_model=IndividualCustomerDetailResponse,
)
def get_individual_customer(
    company_id: int,
    customer_id: int,
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Fetch one individual customer. 404 if the id names a company."""
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.company_id == company_id,
            Customer.type == "Individual",
        )
        .first()
    )

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return detail_response(individual_customer_detail_dict(customer), columns)


@api_router.get(
    "/companies/{company_id}/customers/companies/",
    response_model=list[CompanyCustomerListResponse],
)
def list_company_customers(
    company_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List only the customers that are organisations."""
    query = db.query(Customer).filter(
        Customer.company_id == company_id, Customer.type == "Company"
    )
    query = apply_filters(query, Customer, dict(request.query_params))

    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [company_customer_list_dict(customer) for customer in items]

    return collection_response(response, results, total, total_pages, columns)


@api_router.get(
    "/companies/{company_id}/customers/companies/{customer_id}",
    response_model=CompanyCustomerDetailResponse,
)
def get_company_customer(
    company_id: int,
    customer_id: int,
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Fetch one company customer. 404 if the id names an individual."""
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.company_id == company_id,
            Customer.type == "Company",
        )
        .first()
    )

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return detail_response(company_customer_detail_dict(customer), columns)


# ==========================================
# 4. JOBS RESOURCE ROUTES
# ==========================================


@api_router.get(
    "/companies/{company_id}/jobs/",
    response_model=list[JobListResponse],
)
def list_jobs(
    company_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Retrieve all jobs scoped to a company with filtering and pagination."""
    query = db.query(Job).filter(Job.company_id == company_id)
    query = apply_filters(query, Job, dict(request.query_params))

    items, total, total_pages = paginate_query(query, page, pageSize)

    results = [job_list_dict(job) for job in items]

    return collection_response(response, results, total, total_pages, columns)


@api_router.get(
    "/companies/{company_id}/jobs/{job_id}",
    response_model=JobDetailResponse,
)
def get_job(
    company_id: int,
    job_id: int,
    columns: str | None = Query(None),
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

    return detail_response(job_detail_dict(job), columns)


# ==========================================
# 5. QUOTES RESOURCE ROUTES
# ==========================================


@api_router.get(
    "/companies/{company_id}/quotes/",
    response_model=list[QuoteListResponse],
)
def list_quotes(
    company_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Retrieve all quotes scoped to a company with filtering and pagination."""
    query = db.query(Quote).filter(Quote.company_id == company_id)
    query = apply_filters(query, Quote, dict(request.query_params))

    items, total, total_pages = paginate_query(query, page, pageSize)

    results = [quote_list_dict(quote) for quote in items]

    return collection_response(response, results, total, total_pages, columns)


@api_router.get(
    "/companies/{company_id}/quotes/{quote_id}",
    response_model=QuoteDetailResponse,
)
def get_quote(
    company_id: int,
    quote_id: int,
    columns: str | None = Query(None),
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

    return detail_response(quote_detail_dict(quote), columns)


@api_router.get(
    "/companies/{company_id}/customers/{customer_id}/contacts/",
    response_model=list[ContactListResponse],
)
def list_contacts(
    company_id: int,
    customer_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Contact).filter(
        Contact.company_id == company_id, Contact.customer_id == customer_id
    )
    query = apply_filters(query, Contact, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [contact_list_dict(c) for c in items]
    return collection_response(response, results, total, total_pages, columns)


@api_router.get(
    "/companies/{company_id}/customers/{customer_id}/contacts/{contact_id}",
    response_model=ContactDetailResponse,
)
def get_contact(
    company_id: int,
    customer_id: int,
    contact_id: int,
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
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
    return detail_response(contact_detail_dict(contact), columns)


# ==========================================
# 7. SITES
# ==========================================


@api_router.get("/companies/{company_id}/sites/", response_model=list[SiteListResponse])
def list_sites(
    company_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Site).filter(Site.company_id == company_id)
    query = apply_filters(query, Site, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [site_list_dict(s) for s in items]
    return collection_response(response, results, total, total_pages, columns)


@api_router.get(
    "/companies/{company_id}/sites/{site_id}", response_model=SiteDetailResponse
)
def get_site(
    company_id: int,
    site_id: int,
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    site = (
        db.query(Site).filter(Site.id == site_id, Site.company_id == company_id).first()
    )
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return detail_response(site_detail_dict(site), columns)


# ==========================================
# 8. ASSETS
# ==========================================


@api_router.get(
    "/companies/{company_id}/sites/{site_id}/assets/",
    response_model=list[AssetListResponse],
)
def list_assets(
    company_id: int,
    site_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    pageSize: int = Query(30, ge=1, le=250),
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Asset).filter(
        Asset.company_id == company_id, Asset.site_id == site_id
    )
    query = apply_filters(query, Asset, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [asset_list_dict(a) for a in items]
    return collection_response(response, results, total, total_pages, columns)


@api_router.get(
    "/companies/{company_id}/sites/{site_id}/assets/{asset_id}",
    response_model=AssetDetailResponse,
)
def get_asset(
    company_id: int,
    site_id: int,
    asset_id: int,
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
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
    return detail_response(asset_detail_dict(asset), columns)


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
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Employee).filter(Employee.company_id == company_id)
    query = apply_filters(query, Employee, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [employee_list_dict(e) for e in items]
    return collection_response(response, results, total, total_pages, columns)


@api_router.get(
    "/companies/{company_id}/employees/{employee_id}",
    response_model=EmployeeDetailResponse,
)
def get_employee(
    company_id: int,
    employee_id: int,
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id, Employee.company_id == company_id)
        .first()
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return detail_response(employee_detail_dict(employee), columns)


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
    columns: str | None = Query(None),
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
    return collection_response(response, results, total, total_pages, columns)


@api_router.get(
    "/companies/{company_id}/jobs/{job_id}/notes/{note_id}",
    response_model=JobNoteDetailResponse,
)
def get_job_note(
    company_id: int,
    job_id: int,
    note_id: int,
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
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
    return detail_response(job_note_detail_dict(note), columns)


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
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id, Job.company_id == company_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    query = db.query(Attachment).filter(Attachment.job_id == job_id)
    query = apply_filters(query, Attachment, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [attachment_list_dict(a) for a in items]
    return collection_response(response, results, total, total_pages, columns)


@api_router.get(
    "/companies/{company_id}/jobs/{job_id}/attachments/files/{file_id}",
    response_model=AttachmentDetailResponse,
)
def get_attachment(
    company_id: int,
    job_id: int,
    file_id: str,
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
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
    return detail_response(attachment_detail_dict(attachment), columns)


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
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Status).filter(Status.company_id == company_id)
    query = apply_filters(query, Status, dict(request.query_params))
    items, total, total_pages = paginate_query(query, page, pageSize)
    results = [project_status_code_list_dict(s) for s in items]
    return collection_response(response, results, total, total_pages, columns)


@api_router.get(
    "/companies/{company_id}/setup/statusCodes/projects/{status_code_id}",
    response_model=ProjectStatusCodeDetailResponse,
)
def get_project_status_code(
    company_id: int,
    status_code_id: int,
    columns: str | None = Query(None),
    db: Session = Depends(get_db),
):
    status = (
        db.query(Status)
        .filter(Status.id == status_code_id, Status.company_id == company_id)
        .first()
    )
    if not status:
        raise HTTPException(status_code=404, detail="Project status code not found")
    return detail_response(project_status_code_detail_dict(status), columns)
