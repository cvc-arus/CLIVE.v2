from pydantic import BaseModel, ConfigDict, Field


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


# ---------------------------------------------------------------------------
# Nested wire objects, shared by the responses below. Simpro returns composite
# values as objects, not flat fields; serializers.py composes them from flat
# columns and these classes are the contract they must satisfy.
# ---------------------------------------------------------------------------


class NamedRefSchema(BaseModel):
    """An ``{"ID", "Name"}`` reference."""

    ID: int | None = None
    Name: str | None = None


class StaffRefSchema(BaseModel):
    """A reference to a person who can be assigned work."""

    ID: int | None = None
    Name: str | None = None
    Type: str | None = None
    TypeId: int | None = None


class CompanyAddressSchema(BaseModel):
    """A company's two-line address."""

    Line1: str
    Line2: str


class AddressSchema(BaseModel):
    """A structured postal address."""

    Address: str
    City: str
    State: str
    PostalCode: str
    Country: str


class EmployeeContactSchema(BaseModel):
    """An employee's ``PrimaryContact`` block."""

    Email: str
    SecondaryEmail: str
    WorkPhone: str
    CellPhone: str
    Extension: str
    Fax: str
    PreferredNotificationMethod: str | None = None


class NoteVisibilitySchema(BaseModel):
    """Who may see a job note."""

    Admin: bool
    Customer: bool


class NoteReferenceSchema(BaseModel):
    """What a job note refers to."""

    Text: str
    Number: str | None = None
    Type: str | None = None


class NoteAttachmentSchema(BaseModel):
    """A file attached to a job note."""

    FileName: str
    # The leading underscore is legal as an alias, but not as a field name:
    # Pydantic would treat a field called _href as a private attribute.
    href: str = Field(serialization_alias="_href")


# ---------------------------------------------------------------------------
# Resource responses. Collection routes return a narrow projection and detail
# routes a wide one, so most resources need both.
# ---------------------------------------------------------------------------


class CompanyListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    Name: str


class CompanyDetailResponse(BaseModel):
    """Company configuration. ``Banking`` is out of ADR-013's fidelity scope."""

    model_config = ConfigDict(from_attributes=True)

    ID: int
    Name: str
    Address: CompanyAddressSchema
    BillingAddress: CompanyAddressSchema
    Phone: str
    Fax: str
    Email: str
    Website: str
    Country: str
    Currency: str
    Timezone: str
    TimezoneOffset: str
    CompanyNo: str
    EIN: str
    EmployerTaxRefNo: str
    CISCertNo: str
    Licence: str
    TaxName: str
    DefaultLanguage: str
    DefaultCostCenter: NamedRefSchema | None = None
    SingleCostCenterMode: bool
    SimproPayments: bool
    Template: bool
    MultiCompanyLabel: str | None = None
    MultiCompanyColor: str | None = None
    ScheduleFormat: int
    UIDateFormat: str
    UITimeFormat: str
    DateModified: str


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


class EmployeeListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    Name: str


class EmployeeDetailResponse(BaseModel):
    """``Banking`` and ``PayRates`` are out of ADR-013's fidelity scope."""

    model_config = ConfigDict(from_attributes=True)

    ID: int
    Name: str
    Position: str
    PrimaryContact: EmployeeContactSchema
    Address: AddressSchema
    Zones: list[NamedRefSchema]
    DefaultZone: NamedRefSchema | None = None
    DefaultCompany: NamedRefSchema | None = None
    Archived: bool
    DateCreated: str
    DateModified: str


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    CompanyID: int
    CustomerID: int
    SiteID: int | None = None
    Name: str
    Status: str
    Total: float


class JobNoteListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    Subject: str | None = None
    Reference: NoteReferenceSchema
    Visibility: NoteVisibilitySchema


class JobNoteDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    Subject: str | None = None
    Note: str | None = None
    Reference: NoteReferenceSchema
    Visibility: NoteVisibilitySchema
    DateCreated: str
    FollowUpDate: str | None = None
    Attachments: list[NoteAttachmentSchema]
    SubmittedBy: StaffRefSchema | None = None
    AssignTo: StaffRefSchema | None = None


class AttachmentListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    #: A string upstream, not an integer.
    ID: str
    Filename: str


class AttachmentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: str
    Filename: str
    MimeType: str
    FileSizeBytes: int
    DateAdded: str
    Public: bool
    Email: bool
    Folder: NamedRefSchema | None = None
    AddedBy: StaffRefSchema | None = None


class ProjectStatusCodeListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    Name: str


class ProjectStatusCodeDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    Name: str
    Color: str | None = None
    Priority: int
    DateModified: str
