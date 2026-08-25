from pydantic import BaseModel


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