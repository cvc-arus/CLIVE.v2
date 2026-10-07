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
    # ``alias`` (not ``serialization_alias``) because FastAPI *validates* the
    # dict the serializer returns before serialising it, so the alias has to
    # work in both directions.
    href: str = Field(alias="_href")


class SiteBillingAddressSchema(BaseModel):
    """A site's billing address: the one address shape with no Country."""

    Address: str
    City: str
    State: str
    PostalCode: str


class ContactRefSchema(BaseModel):
    """A nullable pointer at a contact record."""

    ID: int | None = None
    GivenName: str | None = None
    FamilyName: str | None = None
    Email: str | None = None


class CustomerRefSchema(BaseModel):
    """A customer nested in another resource. Carries both name shapes."""

    ID: int
    Type: str
    CompanyName: str
    GivenName: str
    FamilyName: str


class CustomerContactRefSchema(BaseModel):
    """A contact listed on a customer, with its invoicing roles."""

    ID: int
    GivenName: str
    FamilyName: str
    Email: str
    InvoiceContact: bool
    PrimaryInvoiceContact: bool
    StatementContact: bool
    PrimaryStatementContact: bool


class CurrencySchema(BaseModel):
    """A currency. ``ID`` is a string here, not an integer."""

    ID: str
    Name: str
    Visible: bool


class CustomerProfileSchema(BaseModel):
    """A customer's Profile block."""

    Notes: str
    Currency: CurrencySchema
    AccountManager: NamedRefSchema | None = None
    CustomerGroup: NamedRefSchema | None = None
    CustomerProfile: NamedRefSchema | None = None
    ServiceJobCostCenter: NamedRefSchema | None = None


class SitePrimaryContactSchema(BaseModel):
    """A site's primary contact: a named person, not a bundle of numbers."""

    GivenName: str
    FamilyName: str
    Title: str
    Position: str
    Email: str
    WorkPhone: str
    CellPhone: str
    Fax: str
    PreferredNotificationMethod: str
    Contact: ContactRefSchema | None = None


class CustomFieldDefinitionSchema(BaseModel):
    """The definition half of a custom field."""

    ID: int
    Name: str
    Type: str
    IsMandatory: bool
    ListItems: list[str] | None = None


class CustomFieldValueSchema(BaseModel):
    """One custom field paired with its value on a record."""

    CustomField: CustomFieldDefinitionSchema
    Value: str | None = None


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


class CustomerSummaryResponse(BaseModel):
    """A row of the polymorphic /customers/ collection."""

    model_config = ConfigDict(from_attributes=True)

    ID: int
    Type: str
    CompanyName: str
    GivenName: str
    FamilyName: str
    # Underscore is legal as an alias but not as a field name: Pydantic would
    # treat a field called _href as a private attribute. ``alias`` rather than
    # ``serialization_alias`` because FastAPI validates the serializer's dict
    # against this model before serialising it.
    href: str = Field(alias="_href")


class _CustomerDetailBase(BaseModel):
    """Detail fields both customer subtypes share.

    ``Banking`` and ``Rates`` are out of ADR-013's fidelity scope.
    """

    model_config = ConfigDict(from_attributes=True)

    ID: int
    Type: str
    Email: str
    Phone: str
    AltPhone: str
    Address: AddressSchema
    BillingAddress: AddressSchema
    CustomerType: str
    DoNotCall: bool
    Archived: bool
    #: A JSON number on the wire, from a Numeric(12,2) column (ADR-013).
    AmountOwing: float
    Profile: CustomerProfileSchema
    Sites: list[NamedRefSchema]
    Tags: list[NamedRefSchema]
    PreferredTechs: list[StaffRefSchema]
    Contacts: list[CustomerContactRefSchema] | None = None
    Contracts: list[NamedRefSchema] | None = None
    ResponseTimes: list[NamedRefSchema] | None = None
    CustomFields: list[CustomFieldValueSchema]
    DateCreated: str
    DateModified: str


class IndividualCustomerListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    Type: str
    GivenName: str
    FamilyName: str


class IndividualCustomerDetailResponse(_CustomerDetailBase):
    GivenName: str
    FamilyName: str
    Title: str
    CellPhone: str


class CompanyCustomerListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    Type: str
    CompanyName: str


class CompanyCustomerDetailResponse(_CustomerDetailBase):
    CompanyName: str
    CompanyNumber: str
    EIN: str
    Fax: str
    Website: str


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


class ContactListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    GivenName: str
    FamilyName: str


class ContactDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    GivenName: str
    FamilyName: str
    Title: str
    Position: str
    Department: str
    Email: str
    WorkPhone: str
    CellPhone: str
    AltPhone: str
    Fax: str
    Notes: str
    JobContact: bool
    PrimaryJobContact: bool
    QuoteContact: bool
    PrimaryQuoteContact: bool
    InvoiceContact: bool
    PrimaryInvoiceContact: bool
    StatementContact: bool
    PrimaryStatementContact: bool
    Contact: ContactRefSchema | None = None
    CustomFields: list[CustomFieldValueSchema]
    DateModified: str


class SiteListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: int
    Name: str


class SiteDetailResponse(BaseModel):
    """``Rates`` is out of ADR-013's fidelity scope."""

    model_config = ConfigDict(from_attributes=True)

    ID: int
    Name: str
    Address: AddressSchema
    BillingAddress: SiteBillingAddressSchema
    BillingContact: str
    Customers: list[CustomerRefSchema]
    PrimaryContact: SitePrimaryContactSchema
    PublicNotes: str
    PrivateNotes: str
    Zone: NamedRefSchema | None = None
    STCZone: int | None = None
    VEECZone: str | None = None
    PreferredTechs: list[StaffRefSchema]
    PreferredTechnicians: list[NamedRefSchema]
    CustomFields: list[CustomFieldValueSchema]
    Archived: bool
    DateModified: str


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
