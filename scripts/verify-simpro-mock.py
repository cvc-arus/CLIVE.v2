#!/usr/bin/env python3
"""
Manual diagnostic script for the full Simpro mock API.

Not a pytest test - deliberately kept outside tests/ so pytest never
collects it (its helper functions are named test_list_endpoint,
test_single_endpoint, etc., which previously caused pytest to try, and
fail, to run them as real tests). Run it directly against a live mock:

    docker compose up -d simpro-mock
    python scripts/verify_simpro_mock.py

Prints detailed diagnostics on failure and exits non-zero.
"""

import sys

import httpx

BASE_URL = "http://localhost:8100"


def get_token() -> str:
    """Obtain a Bearer token."""
    r = httpx.post(
        f"{BASE_URL}/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "test",
            "client_secret": "test",
        },
    )
    if r.status_code != 200:
        print(f"❌ Token request failed: {r.status_code} - {r.text}")
        sys.exit(1)
    token = r.json()["access_token"]
    print("✅ Token obtained")
    return token


def test_unauthenticated(headers: dict):
    """Verify 401 when no token is sent."""
    r = httpx.get(f"{BASE_URL}/api/v1.0/companies/")
    if r.status_code != 401:
        print(f"❌ Expected 401, got {r.status_code}")
        sys.exit(1)
    print("✅ Unauthenticated request correctly returned 401")


def check_response(r: httpx.Response, resource: str, expect_list: bool = True):
    """Validate status 200, JSON, and optionally list type."""
    if r.status_code != 200:
        print(f"❌ {resource} request failed: {r.status_code}")
        print(f"   Response: {r.text[:500]}")
        sys.exit(1)
    try:
        data = r.json()
    except Exception:
        print(f"❌ {resource} response is not valid JSON: {r.text[:500]}")
        sys.exit(1)
    if expect_list and not isinstance(data, list):
        print(f"❌ {resource} response is not a list: {type(data)}")
        sys.exit(1)
    return data


def test_list_endpoint(
    headers: dict,
    url: str,
    expected_fields: list,
    resource_name: str,
    allow_empty: bool = False,
):
    """Test a list endpoint with field checks and pagination headers."""
    r = httpx.get(url, headers=headers)
    data = check_response(r, resource_name, expect_list=True)
    if not allow_empty and len(data) == 0:
        print(f"⚠️  {resource_name} list is empty (skipping field checks)")
        return
    if len(data) > 0:
        first = data[0]
        for field in expected_fields:
            if field not in first:
                print(
                    f"❌ {resource_name} missing field '{field}'. Keys: {list(first.keys())}"
                )
                sys.exit(1)
    for header in ("Result-Total", "Result-Count", "Result-Pages"):
        if header not in r.headers:
            print(f"❌ Missing pagination header '{header}' for {resource_name}")
            sys.exit(1)
    print(f"✅ {resource_name} list OK (count={len(data)})")


def test_single_endpoint(
    headers: dict,
    url: str,
    expected_fields: list,
    resource_name: str,
):
    """Test a single-item endpoint."""
    r = httpx.get(url, headers=headers)
    data = check_response(r, resource_name, expect_list=False)
    for field in expected_fields:
        if field not in data:
            print(
                f"❌ {resource_name} missing field '{field}'. Keys: {list(data.keys())}"
            )
            sys.exit(1)
    print(f"✅ {resource_name} single OK")


def test_404(headers: dict, url: str, resource_name: str):
    """Test that a non-existent ID returns 404."""
    r = httpx.get(url, headers=headers)
    if r.status_code != 404:
        print(f"❌ {resource_name} expected 404, got {r.status_code} - {r.text[:200]}")
        sys.exit(1)
    print(f"✅ {resource_name} 404 test OK")


def main():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # ---- 1. Unauthenticated ----
    test_unauthenticated(headers)

    # ---- 2. Discover IDs from seeded data ----
    r = httpx.get(f"{BASE_URL}/api/v1.0/companies/", headers=headers)
    companies = check_response(r, "Companies", expect_list=True)
    if len(companies) == 0:
        print("❌ No companies found – did you run the seed script?")
        sys.exit(1)
    company_id = companies[0]["ID"]
    print(f"Using company ID: {company_id}")

    r = httpx.get(
        f"{BASE_URL}/api/v1.0/companies/{company_id}/customers/", headers=headers
    )
    customers = check_response(r, "Customers", expect_list=True)
    if len(customers) == 0:
        print("❌ No customers found – check seed data")
        sys.exit(1)
    customer_id = customers[0]["ID"]
    print(f"Using customer ID: {customer_id}")

    r = httpx.get(f"{BASE_URL}/api/v1.0/companies/{company_id}/sites/", headers=headers)
    sites = check_response(r, "Sites", expect_list=True)
    if len(sites) == 0:
        print("❌ No sites found – check seed data")
        sys.exit(1)
    site_id = sites[0]["ID"]
    print(f"Using site ID: {site_id}")

    r = httpx.get(f"{BASE_URL}/api/v1.0/companies/{company_id}/jobs/", headers=headers)
    jobs = check_response(r, "Jobs", expect_list=True)
    if len(jobs) == 0:
        print("❌ No jobs found – check seed data")
        sys.exit(1)
    job_id = jobs[0]["ID"]
    print(f"Using job ID: {job_id}")

    # ---- 3. All list endpoints ----
    test_list_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/",
        ["ID", "Name"],
        "Companies",
    )
    test_list_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/customers/",
        ["ID", "Type", "CompanyName", "GivenName", "FamilyName", "_href"],
        "Customers",
    )
    test_list_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/customers/{customer_id}/contacts/",
        ["ID", "GivenName", "FamilyName"],
        "Contacts",
    )
    test_list_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/sites/",
        ["ID", "Name"],
        "Sites",
    )
    test_list_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/sites/{site_id}/assets/",
        ["ID", "AssetType"],
        "Assets",
    )
    test_list_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/employees/",
        ["ID", "Name"],
        "Employees",
    )
    test_list_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/jobs/",
        ["ID", "Description", "Total"],
        "Jobs",
    )
    test_list_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/jobs/{job_id}/notes/",
        ["ID", "Subject", "Reference", "Visibility"],
        "JobNotes",
    )
    test_list_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/jobs/{job_id}/attachments/files/",
        ["ID", "Filename"],
        "Attachments",
    )
    test_list_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/quotes/",
        ["ID", "Description", "Total"],
        "Quotes",
    )
    test_list_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/setup/statusCodes/projects/",
        ["ID", "Name"],
        "Project Status Codes",
    )

    # ---- 4. Single endpoints (using discovered IDs) ----
    test_single_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}",
        ["ID", "Name", "Address", "BillingAddress", "Phone", "Timezone",
         "Currency", "DefaultLanguage", "ScheduleFormat", "DateModified"],
        "Company",
    )
    # Simpro publishes no /customers/{id}: the full record lives on a subtype
    # route, which the list response's Type and _href point at (ADR-013).
    test_404(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/customers/{customer_id}",
        "Customer detail (no such route upstream)",
    )
    for subtype, label in (("individuals", "Individual"), ("companies", "Company")):
        r = httpx.get(
            f"{BASE_URL}/api/v1.0/companies/{company_id}/customers/{subtype}/",
            headers=headers,
        )
        rows = check_response(r, f"{label} customers", expect_list=True)
        if not rows:
            print(f"⚠️  No {subtype} customers found, skipping single test")
            continue
        name_field = "CompanyName" if subtype == "companies" else "GivenName"
        test_single_endpoint(
            headers,
            f"{BASE_URL}/api/v1.0/companies/{company_id}/customers/"
            f"{subtype}/{rows[0]['ID']}",
            [
                "ID",
                "Type",
                name_field,
                "Email",
                "Phone",
                "Address",
                "BillingAddress",
                "AmountOwing",
                "Profile",
                "Sites",
                "DateModified",
            ],
            f"{label} customer",
        )

    # Contacts (need a contact ID)
    r = httpx.get(
        f"{BASE_URL}/api/v1.0/companies/{company_id}/customers/{customer_id}/contacts/",
        headers=headers,
    )
    contacts = check_response(r, "Contacts", expect_list=True)
    if contacts:
        cid = contacts[0]["ID"]
        test_single_endpoint(
            headers,
            f"{BASE_URL}/api/v1.0/companies/{company_id}/customers/{customer_id}/contacts/{cid}",
            [
                "ID",
                "GivenName",
                "FamilyName",
                "Title",
                "Position",
                "Department",
                "Email",
                "WorkPhone",
                "CellPhone",
                "JobContact",
                "PrimaryJobContact",
                "InvoiceContact",
                "CustomFields",
                "DateModified",
            ],
            "Contact",
        )
    else:
        print("⚠️  No contacts found, skipping Contact single test")

    # Site
    test_single_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/sites/{site_id}",
        [
            "ID",
            "Name",
            "Address",
            "BillingAddress",
            "BillingContact",
            "Customers",
            "PrimaryContact",
            "PublicNotes",
            "PrivateNotes",
            "Zone",
            "PreferredTechs",
            "CustomFields",
            "Archived",
            "DateModified",
        ],
        "Site",
    )

    # Assets (need asset ID)
    r = httpx.get(
        f"{BASE_URL}/api/v1.0/companies/{company_id}/sites/{site_id}/assets/",
        headers=headers,
    )
    assets = check_response(r, "Assets", expect_list=True)
    if assets:
        aid = assets[0]["ID"]
        test_single_endpoint(
            headers,
            f"{BASE_URL}/api/v1.0/companies/{company_id}/sites/{site_id}/assets/{aid}",
            [
                "ID",
                "AssetType",
                "StartDate",
                "DisplayOrder",
                "Archived",
                "LastTest",
                "CustomFields",
                "DateModified",
            ],
            "Asset",
        )
    else:
        print("⚠️  No assets found, skipping Asset single test")

    # Employees (need employee ID)
    r = httpx.get(
        f"{BASE_URL}/api/v1.0/companies/{company_id}/employees/", headers=headers
    )
    emps = check_response(r, "Employees", expect_list=True)
    if emps:
        eid = emps[0]["ID"]
        test_single_endpoint(
            headers,
            f"{BASE_URL}/api/v1.0/companies/{company_id}/employees/{eid}",
            [
                "ID",
                "Name",
                "Position",
                "PrimaryContact",
                "Address",
                "Zones",
                "DefaultZone",
                "DefaultCompany",
                "Archived",
                "DateCreated",
                "DateModified",
            ],
            "Employee",
        )
    else:
        print("⚠️  No employees found, skipping Employee single test")

    # Job
    test_single_endpoint(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/jobs/{job_id}",
        [
            "ID",
            "Description",
            "Total",
            "Name",
            "Type",
            "Stage",
            "Status",
            "Customer",
            "Site",
            "CustomerContract",
            "Technicians",
            "Tags",
            "Notes",
            "OrderNo",
            "DateIssued",
            "DateModified",
            "ConvertedFrom",
            "CustomFields",
        ],
        "Job",
    )

    # Job Notes
    r = httpx.get(
        f"{BASE_URL}/api/v1.0/companies/{company_id}/jobs/{job_id}/notes/",
        headers=headers,
    )
    notes = check_response(r, "JobNotes", expect_list=True)
    if notes:
        nid = notes[0]["ID"]
        test_single_endpoint(
            headers,
            f"{BASE_URL}/api/v1.0/companies/{company_id}/jobs/{job_id}/notes/{nid}",
            [
                "ID",
                "Subject",
                "Note",
                "Reference",
                "Visibility",
                "DateCreated",
                "FollowUpDate",
                "Attachments",
                "SubmittedBy",
                "AssignTo",
            ],
            "JobNote",
        )
    else:
        print("⚠️  No job notes found, skipping JobNote single test")

    # Attachments
    r = httpx.get(
        f"{BASE_URL}/api/v1.0/companies/{company_id}/jobs/{job_id}/attachments/files/",
        headers=headers,
    )
    atts = check_response(r, "Attachments", expect_list=True)
    if atts:
        atid = atts[0]["ID"]
        test_single_endpoint(
            headers,
            f"{BASE_URL}/api/v1.0/companies/{company_id}/jobs/{job_id}/attachments/files/{atid}",
            [
                "ID",
                "Filename",
                "MimeType",
                "FileSizeBytes",
                "DateAdded",
                "Public",
                "Email",
                "Folder",
                "AddedBy",
            ],
            "Attachment",
        )
    else:
        print("⚠️  No attachments found, skipping Attachment single test")

    # Quotes
    r = httpx.get(
        f"{BASE_URL}/api/v1.0/companies/{company_id}/quotes/", headers=headers
    )
    quotes = check_response(r, "Quotes", expect_list=True)
    if quotes:
        qid = quotes[0]["ID"]
        test_single_endpoint(
            headers,
            f"{BASE_URL}/api/v1.0/companies/{company_id}/quotes/{qid}",
            [
                "ID",
                "Description",
                "Total",
                "Name",
                "Type",
                "Stage",
                "Status",
                "Customer",
                "Site",
                "ValidityDays",
                "IsClosed",
                "DateModified",
                "CustomFields",
            ],
            "Quote",
        )
    else:
        print("⚠️  No quotes found, skipping Quote single test")

    # Project status codes
    r = httpx.get(
        f"{BASE_URL}/api/v1.0/companies/{company_id}/setup/statusCodes/projects/",
        headers=headers,
    )
    statuses = check_response(r, "Project Status Codes", expect_list=True)
    if statuses:
        sid = statuses[0]["ID"]
        test_single_endpoint(
            headers,
            f"{BASE_URL}/api/v1.0/companies/{company_id}/setup/statusCodes/projects/{sid}",
            ["ID", "Name", "Color", "Priority", "DateModified"],
            "Project Status Code",
        )
    else:
        print("⚠️  No project status codes found, skipping single test")

    # ---- 5. 404 tests ----
    bogus = 99999
    test_404(headers, f"{BASE_URL}/api/v1.0/companies/{bogus}", "Company")
    # The subtype routes, not /customers/{id}: that path is not a route at all
    # any more, so it would 404 whatever the id. Tested separately above.
    test_404(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/customers/individuals/{bogus}",
        "Individual customer",
    )
    test_404(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/customers/companies/{bogus}",
        "Company customer",
    )
    test_404(
        headers, f"{BASE_URL}/api/v1.0/companies/{company_id}/sites/{bogus}", "Site"
    )
    test_404(headers, f"{BASE_URL}/api/v1.0/companies/{company_id}/jobs/{bogus}", "Job")
    test_404(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/customers/{customer_id}/contacts/{bogus}",
        "Contact",
    )
    test_404(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/sites/{site_id}/assets/{bogus}",
        "Asset",
    )
    test_404(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/employees/{bogus}",
        "Employee",
    )
    test_404(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/jobs/{job_id}/notes/{bogus}",
        "JobNote",
    )
    test_404(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/jobs/{job_id}/attachments/files/{bogus}",
        "Attachment",
    )
    test_404(
        headers, f"{BASE_URL}/api/v1.0/companies/{company_id}/quotes/{bogus}", "Quote"
    )
    test_404(
        headers,
        f"{BASE_URL}/api/v1.0/companies/{company_id}/setup/statusCodes/projects/{bogus}",
        "Project Status Code",
    )

    print("\n🎉 All integration tests passed!")


if __name__ == "__main__":
    main()
