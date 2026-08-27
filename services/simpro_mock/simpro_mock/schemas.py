from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


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
    ID: int
    Name: str


class CustomerResponse(BaseModel):
    ID: int
    CompanyID: int
    GivenName: str
    FamilyName: str
    Email: str | None = None
    Phone: str | None = None


class JobResponse(BaseModel):
    ID: int
    CompanyID: int
    Name: str
    Status: str
    DateIssued: str | None = None
    Total: float


class QuoteResponse(BaseModel):
    ID: int
    CompanyID: int
    CustomerID: int | None = None
    Name: str
    Status: str
    Total: float


class ContactResponse(BaseModel):
    ID: int
    CompanyID: int
    CustomerID: int
    GivenName: str
    FamilyName: str
    Position: Optional[str] = None
    Email: Optional[str] = None
    Phone: Optional[str] = None

    class Config:
        from_attributes = True


class SiteResponse(BaseModel):
    ID: int
    CompanyID: int
    CustomerID: int
    Name: str
    Address: Optional[str] = None
    City: Optional[str] = None
    Postcode: Optional[str] = None
    State: Optional[str] = None
    Country: Optional[str] = None

    class Config:
        from_attributes = True


class AssetResponse(BaseModel):
    ID: int
    CompanyID: int
    SiteID: int
    AssetNo: str
    Name: str
    SerialNo: Optional[str] = None
    Model: Optional[str] = None
    Manufacturer: Optional[str] = None
    InstalledDate: Optional[str] = None  # ISO date string

    class Config:
        from_attributes = True


class EmployeeResponse(BaseModel):
    ID: int
    CompanyID: int
    GivenName: str
    FamilyName: str
    Position: Optional[str] = None
    Email: Optional[str] = None
    Phone: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    ID: int
    CompanyID: int
    CustomerID: int
    SiteID: Optional[int] = None
    Name: str
    Status: str
    Total: float

    class Config:
        from_attributes = True


class JobNoteResponse(BaseModel):
    ID: int
    JobID: int
    Subject: Optional[str] = None
    Note: Optional[str] = None
    CreatedBy: Optional[int] = None
    CreatedAt: Optional[str] = None  # ISO datetime

    class Config:
        from_attributes = True


class AttachmentResponse(BaseModel):
    ID: int
    JobID: int
    Filename: str
    MimeType: Optional[str] = None
    FileSize: Optional[int] = None
    UploadedAt: Optional[str] = None

    class Config:
        from_attributes = True


class StatusResponse(BaseModel):
    ID: int
    CompanyID: int
    Name: str
    Category: Optional[str] = None
    IsDefault: bool

    class Config:
        from_attributes = True