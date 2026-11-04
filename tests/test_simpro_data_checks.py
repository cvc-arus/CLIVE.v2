"""Offline tests for the W7 data-quality checks (``tests/simpro_data_checks.py``).

Synthetic rows only: no network, no ``.env``, no client data.
"""

import csv
import stat
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests import simpro_data_checks as dq
from tests.simpro_data_checks import Snapshot


def site(
    ident: int,
    name: str = "Site",
    street: str | None = "1 High Street",
    city: str | None = "Leeds",
    postcode: str | None = "LS1 4AP",
    country: str | None = "United Kingdom",
    customers: list[int] | None = None,
    archived: bool = False,
    contact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """A raw site row as Simpro returns it with the audit's projection."""
    return {
        "ID": ident,
        "Name": name,
        "Address": {
            "Address": street,
            "City": city,
            "State": "",
            "PostalCode": postcode,
            "Country": country,
        },
        "Customers": [{"ID": c} for c in ([1] if customers is None else customers)],
        "PrimaryContact": {"GivenName": "A", "FamilyName": "B"}
        if contact is None
        else contact,
        "Archived": archived,
    }


def company(ident: int, name: str = "Acme Ltd", **extra: Any) -> dict[str, Any]:
    """A raw company-customer row."""
    row = {
        "ID": ident,
        "CompanyName": name,
        "Email": f"c{ident}@example.com",
        "Phone": f"0113 496 {ident:04d}",
        "Sites": [{"ID": 100}],
        "Contacts": [{"ID": 900 + ident, "GivenName": "C", "FamilyName": "D"}],
        "Archived": False,
    }
    return {**row, **extra}


def person(ident: int, given: str = "Jo", family: str = "Bloggs", **extra: Any):
    """A raw individual-customer row."""
    row = {
        "ID": ident,
        "GivenName": given,
        "FamilyName": family,
        "Email": f"p{ident}@example.com",
        "Phone": f"0113 496 {ident:04d}",
        "Sites": [{"ID": 100}],
        "Contacts": [],
        "Archived": False,
    }
    return {**row, **extra}


def job(
    ident: int, site_id: int | None = 100, customer_id: int | None = 1, stage="Complete"
):
    """A raw job row; ``None`` IDs give a null reference."""
    return {
        "ID": ident,
        "Stage": stage,
        "Site": None if site_id is None else {"ID": site_id, "Name": "s"},
        "Customer": None if customer_id is None else {"ID": customer_id},
    }


def ids(findings: list[dq.Finding]) -> set:
    return {f.record_id for f in findings}


def groups(findings: list[dq.Finding]) -> set[frozenset]:
    by_group: dict[str, set] = {}
    for f in findings:
        by_group.setdefault(f.group, set()).add(f.record_id)
    return {frozenset(members) for members in by_group.values()}


# --- Edge case 2: blank values -----------------------------------------------


@pytest.mark.parametrize("value", [None, "", "   ", "\xa0", " \xa0\t\n", [], {}])
def test_blank_values(value):
    assert dq.is_blank(value)


@pytest.mark.parametrize("value", ["x", 0, False, [1], {"a": 1}])
def test_non_blank_values(value):
    assert not dq.is_blank(value)


# --- Edge case 5: normalisation ----------------------------------------------


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("12 High Street", "12  high st."),
        ("Café Rouge", "cafe rouge"),
        ("Smith & Sons", "Smith and Sons"),
        ("O'Brien Road", "OBrien Rd"),
        ("Main Avenue", "MAIN AVE"),
    ],
)
def test_norm_text_folds_equivalent_forms(a, b):
    assert dq.norm_text(a) == dq.norm_text(b)


def test_norm_text_keeps_numbers_apart():
    """Edge case 4: unit and street numbers stay in the key."""
    assert dq.norm_text("Unit 1, 5 High St") != dq.norm_text("Unit 2, 5 High St")


@pytest.mark.parametrize(
    ("a", "b"),
    [("Acme Ltd", "ACME Limited"), ("Acme", "Acme Ltd."), ("Acme PLC", "acme")],
)
def test_company_name_key_drops_legal_form(a, b):
    assert dq.company_name_key(a) == dq.company_name_key(b)


def test_company_name_key_keeps_a_lone_suffix_word():
    assert dq.company_name_key("Ltd") == "ltd"


# --- Edge case 6: UK postcodes -----------------------------------------------


@pytest.mark.parametrize(
    "postcode",
    [
        "SW1A 1AA",
        "sw1a1aa",
        "SW1A  1AA",
        " M1 1AE ",
        "B33 8TH",
        "CR2 6XH",
        "DN55 1PT",
        "W1A 0AX",
        "EC1A 1BB",
        "GIR 0AA",
        "BT1 5GS",
        "JE2 3QA",
        "GY1 1AA",
        "IM1 1AA",
        "LS1\xa04AP",
    ],
)
def test_valid_uk_postcodes(postcode):
    assert dq.is_uk_postcode(postcode)


@pytest.mark.parametrize(
    "postcode",
    [
        "",
        None,
        "SW1A",
        "BFPO 123",
        "SW1A-1AA",
        "12345",
        "SW1A 1AC",
        "SW1A 1AI",
        "Q1 1AA1",
        "LS1 4A",
    ],
)
def test_invalid_uk_postcodes(postcode):
    assert not dq.is_uk_postcode(postcode)


@pytest.mark.parametrize(
    "country",
    [
        None,
        "",
        "UK",
        "gb",
        "United Kingdom",
        "England",
        "Scotland",
        "Wales",
        "Northern Ireland",
        "Great Britain",
        "U.K.",
    ],
)
def test_uk_countries(country):
    assert dq.is_uk_country(country)


@pytest.mark.parametrize("country", ["Ireland", "France", "USA"])
def test_non_uk_countries(country):
    assert not dq.is_uk_country(country)


def test_s5b_and_s5c_split_on_country():
    snap = Snapshot(
        sites=[
            site(1, postcode="SW1A 1AA"),
            site(2, postcode="BFPO 123"),
            site(3, postcode="D02 X285", country="Ireland"),
            site(4, postcode="", country=None),
        ]
    )
    assert ids(dq.check_s5b_site_bad_postcode(snap)) == {2}
    assert ids(dq.check_s5c_site_non_uk(snap)) == {3}
    assert ids(dq.check_s5a_site_incomplete_address(snap)) == {4}


def test_s5a_names_every_blank_part():
    snap = Snapshot(sites=[site(1, street=" ", city=None, postcode="\xa0")])
    (finding,) = dq.check_s5a_site_incomplete_address(snap)
    assert finding.reason == "blank street, city, postcode"


def test_s5a_handles_a_null_address_block():
    row = site(1)
    row["Address"] = None
    assert ids(dq.check_s5a_site_incomplete_address(Snapshot(sites=[row]))) == {1}


# --- Edge case 1: projections ------------------------------------------------


def test_projection_absent_from_every_row_raises():
    rows = [{"ID": 1}, {"ID": 2}]
    with pytest.raises(dq.ProjectionError, match=r"\['Customers'\]"):
        dq.check_projection(rows, ["ID", "Customers"])


def test_projection_absent_from_some_rows_is_counted():
    rows = [{"ID": 1, "Customers": []}, {"ID": 2}]
    assert dq.check_projection(rows, ["ID", "Customers"]) == {"ID": 0, "Customers": 1}


def test_projection_present_but_null_is_not_absent():
    rows = [{"ID": 1, "Customers": None}]
    assert dq.check_projection(rows, ["Customers"]) == {"Customers": 0}


def test_projection_on_no_rows_does_not_raise():
    assert dq.check_projection([], ["ID"]) == {"ID": 0}


def test_projection_error_message_holds_names_only():
    rows = [{"ID": 1, "Name": "Secret Customer Site"}]
    with pytest.raises(dq.ProjectionError) as exc:
        dq.check_projection(rows, ["Address"])
    assert "Secret" not in str(exc.value)


# --- Edge case 8: de-duplication ---------------------------------------------


def test_dedupe_keeps_first_and_counts_repeats():
    rows = [{"ID": 1, "v": "a"}, {"ID": 2}, {"ID": 1, "v": "b"}, {"ID": 1}]
    unique, dropped = dq.dedupe_by_id(rows)
    assert [r["ID"] for r in unique] == [1, 2]
    assert unique[0]["v"] == "a"
    assert dropped == 2


# --- Sites -------------------------------------------------------------------


@pytest.mark.parametrize(
    "customers", [[], None, [{"ID": None}], [{"Name": "x"}], [{"ID": 0}], "junk"]
)
def test_s1_site_without_usable_customer(customers):
    row = site(1)
    row["Customers"] = customers
    assert ids(dq.check_s1_site_no_customer(Snapshot(sites=[row]))) == {1}


def test_s1_ignores_site_with_customer():
    assert dq.check_s1_site_no_customer(Snapshot(sites=[site(1)])) == []


def test_s2_missing_and_archived_customers():
    snap = Snapshot(
        sites=[site(1, customers=[1]), site(2, customers=[2]), site(3, customers=[3])],
        company_customers=[company(1), company(2, Archived=True)],
    )
    reasons = {f.record_id: f.reason for f in dq.check_s2_site_bad_customer(snap)}
    assert reasons == {2: "customer 2 archived", 3: "customer 3 not found"}


def test_s3a_exact_duplicates_after_normalisation():
    snap = Snapshot(
        sites=[
            site(1, "Acme HQ", "12 High Street", postcode="LS1 4AP"),
            site(2, "ACME  hq", "12 high st", postcode="ls14ap"),
            site(3, "Acme HQ", "14 High Street", postcode="LS1 4AP"),
        ]
    )
    assert groups(dq.check_s3a_site_exact_duplicates(snap)) == {frozenset({1, 2})}


def test_s3a_blank_addresses_never_match():
    """Edge case 3."""
    snap = Snapshot(
        sites=[
            site(1, "Same", street="", postcode=""),
            site(2, "Same", street=None, postcode=None, city=None),
        ]
    )
    assert dq.check_s3a_site_exact_duplicates(snap) == []
    assert dq.check_s3b_site_shared_address(snap) == []


def test_s3a_postcode_alone_is_not_an_address():
    snap = Snapshot(sites=[site(1, "A", street=""), site(2, "A", street="")])
    assert dq.check_s3a_site_exact_duplicates(snap) == []


def test_s3a_falls_back_to_city_without_postcode():
    snap = Snapshot(
        sites=[site(1, "A", postcode=None), site(2, "A", postcode="", city="LEEDS")]
    )
    assert groups(dq.check_s3a_site_exact_duplicates(snap)) == {frozenset({1, 2})}


def test_s3_units_are_different_sites():
    """Edge case 4."""
    snap = Snapshot(
        sites=[
            site(1, "Shop", "Unit 1, 5 High St"),
            site(2, "Shop", "Unit 2, 5 High St"),
        ]
    )
    assert dq.check_s3a_site_exact_duplicates(snap) == []
    assert dq.check_s3b_site_shared_address(snap) == []


def test_s3b_shared_address_with_different_names():
    snap = Snapshot(
        sites=[
            site(1, "Shop A", "Retail Park"),
            site(2, "Shop B", "Retail Park"),
            site(3, "Shop A", "Retail Park"),
            site(4, "Lonely", "Elsewhere"),
        ]
    )
    assert groups(dq.check_s3b_site_shared_address(snap)) == {frozenset({1, 2, 3})}


def test_s3b_same_name_same_address_is_only_s3a():
    snap = Snapshot(sites=[site(1, "A"), site(2, "a")])
    assert dq.check_s3b_site_shared_address(snap) == []


@pytest.mark.parametrize(
    ("a", "b", "similar"),
    [
        ("acme warehouse", "acme warehose", True),
        ("acme warehouse", "acme warehouse", True),
        ("12 high st", "14 high st", False),
        ("unit 1 acme", "unit 2 acme", False),
        ("acme", "zenith", False),
        ("", "", False),
    ],
)
def test_similar_names(a, b, similar):
    assert dq.similar_names(a, b) is similar


def test_s3c_similar_name_different_address():
    snap = Snapshot(
        sites=[
            site(1, "Acme Warehouse", "1 Road"),
            site(2, "Acme Warehose", "2 Road"),
            site(3, "Acme Warehouse", "1 Road"),
        ]
    )
    # 1 and 3 share an address (S3a's job), but 3 still links to 2.
    assert groups(dq.check_s3c_site_similar_names(snap)) == {frozenset({1, 2, 3})}


def test_s3c_blank_address_counts_as_different():
    snap = Snapshot(sites=[site(1, "Acme"), site(2, "Acme", street="")])
    assert groups(dq.check_s3c_site_similar_names(snap)) == {frozenset({1, 2})}


def test_s3c_oversized_block_compares_exact_names_only(monkeypatch):
    monkeypatch.setattr(dq, "FUZZY_BLOCK_LIMIT", 2)
    rows = [
        site(1, "Acme One", "1 A"),
        site(2, "Acme One", "2 A"),
        site(3, "Acme Onee", "3 A"),
    ]
    found, skipped = dq.s3c_groups(rows)
    assert skipped == 1
    assert [g for g in found if len(g) > 1] == [{1, 2}]


def test_s4_site_with_no_assets():
    snap = Snapshot(sites=[site(1), site(2)], assets={1: [], 2: [{"ID": 5}]})
    assert ids(dq.check_s4_site_no_assets(snap)) == {1}


def test_s4_unscanned_site_is_an_error_not_a_finding():
    snap = Snapshot(sites=[site(1), site(2)], assets={1: []})
    with pytest.raises(dq.ProjectionError, match="1 sites were not scanned"):
        dq.check_s4_site_no_assets(snap)


@pytest.mark.parametrize(
    ("name", "flagged"),
    [
        ("", True),
        ("  ", True),
        ("-", True),
        ("TBC", True),
        ("test", True),
        ("N/A", True),
        ("Do NOT use - old", True),
        ("DUPLICATE of 12", True),
        ("Test Valley Depot", False),
        ("Acme", False),
        ("Unknown Pleasures Ltd", False),
    ],
)
def test_s6_placeholder_names(name, flagged):
    snap = Snapshot(sites=[site(1, name)])
    assert bool(dq.check_s6_site_placeholder_name(snap)) is flagged


def test_s7_dormant_counts_jobs_and_quotes_in_both_companies():
    snap = Snapshot(
        sites=[site(1), site(2), site(3), site(4, archived=True)],
        jobs=[job(10, site_id=1)],
        quotes=[{"ID": 20, "Site": {"ID": 2}, "Customer": {"ID": 1}}],
    )
    assert ids(dq.check_s7_site_dormant(snap)) == {3}


@pytest.mark.parametrize(
    ("contact", "flagged"),
    [
        (None, True),
        ({}, True),
        ({"GivenName": " ", "FamilyName": None, "Email": ""}, True),
        ({"GivenName": "Jo"}, False),
        ({"Email": "x@y.com"}, False),
    ],
)
def test_s8_primary_contact(contact, flagged):
    row = site(1)
    row["PrimaryContact"] = contact
    assert bool(dq.check_s8_site_no_primary_contact(Snapshot(sites=[row]))) is flagged


def test_s9_counts_distinct_customers():
    snap = Snapshot(sites=[site(1, customers=[1, 2]), site(2, customers=[1, 1])])
    assert ids(dq.check_s9_site_many_customers(snap)) == {1}


@pytest.mark.parametrize(
    ("stage", "open_"),
    [
        ("Pending", True),
        ("Progress", True),
        ("Complete", False),
        ("Invoiced", False),
        ("Archived", False),
        (None, False),
    ],
)
def test_s10_open_job_stages(stage, open_):
    snap = Snapshot(
        sites=[site(1, archived=True)], jobs=[job(1, site_id=1, stage=stage)]
    )
    assert bool(dq.check_s10_archived_site_open_work(snap)) is open_


@pytest.mark.parametrize(
    ("stage", "closed", "open_"),
    [
        ("InProgress", False, True),
        ("InProgress", None, True),
        ("InProgress", True, False),
        ("Complete", False, False),
        ("Approved", False, False),
    ],
)
def test_s10_open_quote_stages(stage, closed, open_):
    quote = {"ID": 1, "Stage": stage, "IsClosed": closed, "Site": {"ID": 1}}
    snap = Snapshot(sites=[site(1, archived=True)], quotes=[quote])
    assert bool(dq.check_s10_archived_site_open_work(snap)) is open_


def test_archived_is_only_literal_true():
    """Edge case 7: archived rows are flagged, never dropped or guessed."""
    assert dq.is_archived({"Archived": True})
    for value in (False, None, "true", 1):
        assert not dq.is_archived({"Archived": value})
    snap = Snapshot(sites=[site(1, customers=[], archived=True)])
    (finding,) = dq.check_s1_site_no_customer(snap)
    assert finding.fields["archived"] is True


# --- Customers ---------------------------------------------------------------


def test_c1_customer_with_no_sites_either_way():
    snap = Snapshot(
        sites=[site(100, customers=[2])],
        company_customers=[company(1, Sites=[]), company(2, Sites=[]), company(3)],
    )
    # 2 has an empty list but a site links to it, so it is not orphaned.
    assert ids(dq.check_c1_customer_no_sites(snap)) == {1}


def test_c2_only_companies_need_contacts():
    snap = Snapshot(
        company_customers=[company(1, Contacts=[]), company(2)],
        individual_customers=[person(3)],
    )
    assert ids(dq.check_c2_customer_no_contacts(snap)) == {1}


def test_c3_company_duplicates_by_name():
    snap = Snapshot(
        company_customers=[
            company(1, "Acme Ltd"),
            company(2, "ACME Limited"),
            company(3, "Acme Security"),
            company(4, ""),
            company(5, ""),
        ]
    )
    assert groups(dq.check_c3_customer_duplicates(snap)) == {frozenset({1, 2})}


def test_c3_individuals_need_name_and_shared_contact_detail():
    snap = Snapshot(
        individual_customers=[
            person(1, Email="jo@x.com"),
            person(2, Email="JO@x.com "),
            person(3, Email="other@x.com", Phone="0113 000 0000"),
            person(4, "Sam", Email="jo@x.com"),
        ]
    )
    assert groups(dq.check_c3_customer_duplicates(snap)) == {frozenset({1, 2})}


def test_c4_shared_email_or_phone_across_customers():
    snap = Snapshot(
        company_customers=[
            company(1, Email="a@x.com", Phone="+44 113 496 0000"),
            company(2, "B", Email="b@x.com", Phone="0113 4960000"),
            company(3, "C", Email="A@X.com", Phone=""),
            company(4, "D", Email="d@x.com", Phone="123"),
            company(5, "E", Email="e@x.com", Phone="123"),
        ]
    )
    # 4 and 5 share "123", too short to compare.
    assert groups(dq.check_c4_customer_shared_contact_details(snap)) == {
        frozenset({1, 2, 3})
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("+44 (0)113 496 0000", "01134960000"),
        ("+44 113 496 0000", "01134960000"),
        ("0113-496-0000", "01134960000"),
        ("12345", ""),
        (None, ""),
    ],
)
def test_norm_phone(raw, expected):
    assert dq.norm_phone(raw) == expected


def test_c5_needs_every_channel_blank():
    snap = Snapshot(
        company_customers=[
            company(1, Email="", Phone=" "),
            company(2, Email="", Phone="", AltPhone="0113 496 0000"),
        ],
        individual_customers=[
            person(3, Email=None, Phone=None, CellPhone="07700 900000")
        ],
    )
    assert ids(dq.check_c5_customer_uncontactable(snap)) == {1}


def test_c6_blank_names():
    snap = Snapshot(
        company_customers=[company(1, "  "), company(2)],
        individual_customers=[person(3, given=""), person(4)],
    )
    reasons = {f.record_id: f.reason for f in dq.check_c6_customer_blank_name(snap)}
    assert reasons == {1: "blank company name", 3: "blank GivenName"}


@pytest.mark.parametrize(
    ("email", "problem"),
    [
        ("a@b.co.uk", None),
        ("", None),
        (None, None),
        ("a@b", "malformed email"),
        ("a b@c.com", "malformed email"),
        ("a@b.com.", "malformed email"),
        ("a@b.com; c@d.com", "more than one address in the field"),
        ("a@b.com,c@d.com", "more than one address in the field"),
        ("a@b@c.com", "more than one address in the field"),
    ],
)
def test_email_problem(email, problem):
    assert dq.email_problem(email) == problem


def test_c8_archived_customer_with_active_links():
    snap = Snapshot(
        sites=[site(100, customers=[1]), site(101, customers=[2], archived=True)],
        company_customers=[
            company(1, Archived=True),
            company(2, "B", Archived=True),
            company(3, "C", Archived=True),
        ],
        jobs=[job(1, customer_id=3, stage="Progress")],
    )
    assert ids(dq.check_c8_archived_customer_active_links(snap)) == {1, 3}


def test_c9_list_consistency():
    snap = Snapshot(
        company_customers=[company(1), company(2)],
        individual_customers=[person(2), person(3)],
        summary_customer_ids={1, 2, 4},
        summary_customer_total=5,
    )
    reasons = {
        (f.record_id, f.reason) for f in dq.check_c9_customer_list_consistency(snap)
    }
    assert reasons == {
        (2, "listed as both company and individual"),
        (4, "in summary list, in neither subtype list"),
        (3, "in a subtype list, not in summary list"),
        ("totals", "summary total 5 != companies + individuals 3"),
    }


def test_c9_consistent_lists_have_no_findings():
    snap = Snapshot(
        company_customers=[company(1)],
        individual_customers=[person(2)],
        summary_customer_ids={1, 2},
        summary_customer_total=2,
    )
    assert dq.check_c9_customer_list_consistency(snap) == []


# --- Contacts ----------------------------------------------------------------


def test_ct1_duplicates_within_one_customer_only():
    contacts = [
        {"ID": 1, "GivenName": "Jo", "FamilyName": "Bloggs"},
        {"ID": 2, "GivenName": "JO", "FamilyName": "bloggs "},
        {"ID": 3, "GivenName": "Sam", "FamilyName": "X", "Email": "s@x.com"},
        {"ID": 4, "GivenName": "Samuel", "FamilyName": "X", "Email": "S@x.com"},
        {"ID": 5, "GivenName": "", "FamilyName": "", "Email": ""},
        {"ID": 6, "GivenName": "", "FamilyName": "", "Email": None},
    ]
    other = [{"ID": 7, "GivenName": "Jo", "FamilyName": "Bloggs"}]
    snap = Snapshot(
        company_customers=[
            company(1, Contacts=contacts),
            company(2, "B", Contacts=other),
        ]
    )
    assert groups(dq.check_ct1_contact_duplicates(snap)) == {
        frozenset({1, 2}),
        frozenset({3, 4}),
    }


def test_ct2_blank_contact_names():
    contacts = [
        {"ID": 1, "GivenName": " ", "FamilyName": None},
        {"ID": 2, "GivenName": "Jo", "FamilyName": ""},
        {"GivenName": "", "FamilyName": ""},
    ]
    snap = Snapshot(company_customers=[company(1, Contacts=contacts)])
    assert ids(dq.check_ct2_contact_blank_name(snap)) == {1}


def test_contacts_tolerate_null_or_junk_lists():
    snap = Snapshot(
        company_customers=[company(1, Contacts=None), company(2, "B", Contacts=["x"])]
    )
    assert dq.check_ct1_contact_duplicates(snap) == []
    assert dq.check_ct2_contact_blank_name(snap) == []


# --- Assets ------------------------------------------------------------------


def test_a1_parent_checks():
    snap = Snapshot(
        assets={
            1: [
                {"ID": 10, "ParentID": None},
                {"ID": 11, "ParentID": 10},
                {"ID": 12, "ParentID": 99},
                {"ID": 13, "ParentID": 13},
                {"ID": 14, "ParentID": 0},
            ],
            2: [{"ID": 20, "ParentID": 10}],
        }
    )
    reasons = {f.record_id: f.reason for f in dq.check_a1_asset_bad_parent(snap)}
    assert reasons == {
        12: "parent 99 not on this site",
        13: "asset is its own parent",
        20: "parent 10 not on this site",
    }


def test_a2_active_assets_on_archived_site():
    snap = Snapshot(
        sites=[site(1, archived=True), site(2)],
        assets={
            1: [{"ID": 10, "Archived": False}, {"ID": 11, "Archived": True}],
            2: [{"ID": 20}],
        },
    )
    assert ids(dq.check_a2_asset_on_archived_site(snap)) == {10}


# --- Jobs and quotes ---------------------------------------------------------


def test_j1_link_problems():
    snap = Snapshot(
        sites=[site(100)],
        company_customers=[company(1)],
        jobs=[
            job(1),
            job(2, site_id=None),
            job(3, site_id=555),
            job(4, customer_id=None),
            job(5, site_id=None, customer_id=777),
        ],
    )
    reasons = {f.record_id: f.reason for f in dq.check_j1_job_links(snap)}
    assert reasons == {
        2: "no site",
        3: "site 555 not found",
        4: "no customer",
        5: "no site; customer 777 not found",
    }


def test_q1_and_q2_use_the_quote_list():
    snap = Snapshot(
        sites=[site(100, customers=[1])],
        company_customers=[company(1), company(2, "B")],
        quotes=[job(1, site_id=None), job(2, customer_id=2)],
    )
    assert ids(dq.check_q1_quote_links(snap)) == {1}
    assert ids(dq.check_q2_quote_customer_not_on_site(snap)) == {2}


def test_j2_skips_unknown_site_and_missing_customer():
    snap = Snapshot(
        sites=[site(100, customers=[1])],
        jobs=[
            job(1, customer_id=2),
            job(2, site_id=555, customer_id=2),
            job(3, customer_id=None),
            job(4),
        ],
    )
    assert ids(dq.check_j2_job_customer_not_on_site(snap)) == {1}


def test_x1_site_sets():
    snap = Snapshot(sites=[site(1), site(2)], other_company_site_ids={2, 3})
    reasons = {(f.record_id, f.reason) for f in dq.check_x1_site_sets_differ(snap)}
    assert reasons == {
        (1, "site only in the service company"),
        (3, "site only in the projects company"),
    }


# --- Edge case 12: groups ----------------------------------------------------


def test_group_labels_are_deterministic_and_skip_singletons():
    labels = dq._groups("S3a", [{9, 4}, {7}, {2, 3, 8}])
    assert labels == {
        2: "S3a-0001",
        3: "S3a-0001",
        8: "S3a-0001",
        4: "S3a-0002",
        9: "S3a-0002",
    }


def test_every_check_runs_on_an_empty_snapshot():
    for check, func in dq.CHECKS.items():
        assert func(Snapshot()) == [], check


def test_every_finding_carries_its_own_check_id():
    snap = Snapshot(
        sites=[site(1, "", customers=[], archived=True), site(2, "", customers=[9, 8])],
        jobs=[job(1, site_id=1, customer_id=None, stage="Pending")],
        quotes=[job(2, site_id=2, customer_id=5)],
        assets={1: [{"ID": 3, "ParentID": 4}], 2: []},
        company_customers=[
            company(5, "", Contacts=[], Sites=[], Email="bad", Archived=True)
        ],
        summary_customer_total=7,
    )
    for check, func in dq.CHECKS.items():
        for finding in func(snap):
            assert finding.check == check


# --- Report writer: edge cases 9, 11 and the git guard -----------------------


@pytest.fixture
def ignored_dir(tmp_path: Path) -> Path:
    """A git repo whose ``private/`` folder is ignored."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("private/\n")
    return tmp_path / "private" / "data-audit" / "2026-11-03"


def test_writer_refuses_a_tracked_location(tmp_path: Path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    with pytest.raises(RuntimeError, match="not git-ignored"):
        dq.ReportWriter(tmp_path / "public" / "report")
    assert not (tmp_path / "public").exists()


def test_writer_refuses_outside_any_repo(tmp_path: Path):
    with pytest.raises(RuntimeError, match="not git-ignored"):
        dq.ReportWriter(tmp_path / "report")


def test_writer_permissions(ignored_dir: Path):
    writer = dq.ReportWriter(ignored_dir)
    writer.write_check("S1", [dq.Finding("S1", 1, "no customer", {"name": "x"})])
    assert stat.S_IMODE(ignored_dir.stat().st_mode) == 0o700
    for path in ignored_dir.iterdir():
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_summary_is_incomplete_until_finished(ignored_dir: Path):
    writer = dq.ReportWriter(ignored_dir)
    summary = ignored_dir / "summary.md"
    assert "INCOMPLETE" in summary.read_text()
    writer.write_check("S1", [])
    assert "INCOMPLETE" in summary.read_text()
    writer.finish(["S1", "S2"])
    assert "INCOMPLETE" in summary.read_text()
    writer.write_check("S2", [])
    writer.finish(["S1", "S2"])
    assert "audit: COMPLETE" in summary.read_text()


def test_summary_stays_incomplete_after_an_error(ignored_dir: Path):
    writer = dq.ReportWriter(ignored_dir)
    writer.write_check("S1", [])
    writer.record_error("S4", "1 sites were not scanned for assets")
    writer.finish(["S1"])
    text = (ignored_dir / "summary.md").read_text()
    assert "INCOMPLETE" in text
    assert "| S4 | ERROR: 1 sites were not scanned for assets |" in text


def test_csv_is_sorted_and_formula_safe(ignored_dir: Path):
    writer = dq.ReportWriter(ignored_dir)
    findings = [
        dq.Finding("S3a", 10, "dup", {"name": "=HYPERLINK(1)"}, "S3a-0002"),
        dq.Finding("S3a", 9, "dup", {"name": "+44"}, "S3a-0001"),
        dq.Finding("S3a", 100, "dup", {"name": "@x", "extra": None}, "S3a-0001"),
    ]
    writer.write_check("S3a", findings)
    with (ignored_dir / "S3a.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["check", "group", "record_id", "reason", "name", "extra"]
    assert [r[2] for r in rows[1:]] == ["9", "100", "10"]
    assert [r[4] for r in rows[1:]] == ["'+44", "'@x", "'=HYPERLINK(1)"]


@pytest.mark.parametrize(
    ("value", "cell"),
    [(None, ""), ("ok", "ok"), ("-5", "'-5"), ("=1+1", "'=1+1"), (3, "3")],
)
def test_safe_cell(value, cell):
    assert dq.safe_cell(value) == cell
