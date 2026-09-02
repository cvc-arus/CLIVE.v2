from pydantic import BaseModel, ConfigDict


# Response shape for the mock OAuth2 token endpoint
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


# Response shape for the health check endpoint
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    Name: str


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    CompanyID: int
    GivenName: str
    FamilyName: str
    Email: str | None = None
    Phone: str | None = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    CompanyID: int
    Name: str
    Status: str
    DateIssued: str | None = None
    Total: float


class QuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    CompanyID: int
    CustomerID: int | None = None
    Name: str
    Status: str
    Total: float


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    CompanyID: int
    CustomerID: int
    GivenName: str
    FamilyName: str
    Position: str | None = None
    Email: str | None = None
    Phone: str | None = None


class SiteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    CompanyID: int
    CustomerID: int
    Name: str
    Address: str | None = None
    City: str | None = None
    Postcode: str | None = None
    State: str | None = None
    Country: str | None = None


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    CompanyID: int
    SiteID: int
    AssetNo: str
    Name: str
    SerialNo: str | None = None
    Model: str | None = None
    Manufacturer: str | None = None
    InstalledDate: str | None = None  # ISO date string


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    CompanyID: int
    GivenName: str
    FamilyName: str
    Position: str | None = None
    Email: str | None = None
    Phone: str | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    CompanyID: int
    CustomerID: int
    SiteID: int | None = None
    Name: str
    Status: str
    Total: float


class JobNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    JobID: int
    Subject: str | None = None
    Note: str | None = None
    CreatedBy: int | None = None
    CreatedAt: str | None = None  # ISO datetime


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    JobID: int
    Filename: str
    MimeType: str | None = None
    FileSize: int | None = None
    UploadedAt: str | None = None


class StatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    CompanyID: int
    Name: str
    Category: str | None = None
    IsDefault: bool
