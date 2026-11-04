"""Data-quality checks for CVC's Simpro data (course correction W7).

Pure functions over **raw** payload rows (the JSON dicts Simpro returns), not
validated models: a model turns a missing key and ``null`` into the same
``None``, and the audit has to tell them apart (a key missing from every row
means Simpro ignored a ``columns`` projection; see :func:`check_projection`).

The live module ``tests/test_live_data_quality.py`` fetches a
:class:`Snapshot` and runs every check in :data:`CHECKS`; the offline module
``tests/test_simpro_data_checks.py`` proves the edge cases on synthetic rows.
Nothing here touches the network, and nothing here prints: findings hold
client data and go only to the private report (:class:`ReportWriter`).
"""

import csv
import difflib
import os
import re
import subprocess
import unicodedata
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

Row = Mapping[str, Any]

#: Job stages that count as open work (contract enum: Pending, Progress,
#: Complete, Invoiced, Archived).
OPEN_JOB_STAGES = frozenset({"Pending", "Progress"})

#: Quote stages that count as open, when ``IsClosed`` is not true (contract
#: enum: InProgress, Complete, Approved).
OPEN_QUOTE_STAGES = frozenset({"InProgress"})

#: Word folds applied after normalisation. Conservative on purpose: only
#: abbreviations that cannot change which place or business is meant.
WORD_FOLDS = {
    "street": "st",
    "road": "rd",
    "avenue": "ave",
    "drive": "dr",
    "lane": "ln",
    "close": "cl",
    "court": "ct",
    "place": "pl",
    "crescent": "cres",
    "limited": "ltd",
}

#: Legal-form words dropped from the end of a company name before comparing.
LEGAL_SUFFIXES = frozenset({"ltd", "plc", "llp", "inc"})

#: Normalised names that mean "not a real name".
PLACEHOLDER_NAMES = frozenset(
    {"test", "tbc", "tba", "unknown", "na", "n a", "none", "x", "xx", "xxx"}
)

#: Normalised name prefixes that mark a record as not to be used.
PLACEHOLDER_PREFIXES = ("do not use", "dont use", "duplicate", "delete")

#: Country values that mean the UK, normalised to letters only.
UK_COUNTRIES = frozenset(
    {
        "uk",
        "gb",
        "unitedkingdom",
        "greatbritain",
        "england",
        "scotland",
        "wales",
        "northernireland",
    }
)

#: A full UK postcode with all whitespace removed. The inward code's letters
#: never include C, I, K, M, O or V. ``GIR0AA`` is the one special case.
UK_POSTCODE = re.compile(r"(GIR0AA|[A-Z]{1,2}[0-9][A-Z0-9]?[0-9][ABD-HJLNP-UW-Z]{2})")

EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s.]+")

#: Fuzzy name matches (S3c) need at least this ``SequenceMatcher`` ratio.
FUZZY_RATIO = 0.9

#: Fuzzy blocks larger than this are not compared pairwise; they are counted
#: in the summary instead, so the cost stays bounded.
FUZZY_BLOCK_LIMIT = 400

#: Phone numbers with fewer digits than this are not compared (C4).
MIN_PHONE_DIGITS = 7

#: Characters that make a spreadsheet treat a cell as a formula.
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


class ProjectionError(Exception):
    """A requested ``columns`` field is absent from every row.

    Raised instead of reporting every row as blank. The message holds field
    names only, never values.
    """


@dataclass(frozen=True)
class Finding:
    """One record that failed one check.

    ``fields`` holds what Alex needs to find and fix the record; it is
    written only to the private report.
    """

    check: str
    record_id: int | str
    reason: str
    fields: Mapping[str, Any] = field(default_factory=dict)
    group: str = ""


@dataclass
class Snapshot:
    """Everything one audit run fetched, as raw rows de-duplicated by ID.

    ``assets`` maps a site ID to its asset rows; a site with no entry was not
    scanned, which is an incomplete run, not "no assets".
    """

    sites: list[dict[str, Any]] = field(default_factory=list)
    other_company_site_ids: set[int] = field(default_factory=set)
    company_customers: list[dict[str, Any]] = field(default_factory=list)
    individual_customers: list[dict[str, Any]] = field(default_factory=list)
    summary_customer_ids: set[int] = field(default_factory=set)
    summary_customer_total: int = 0
    jobs: list[dict[str, Any]] = field(default_factory=list)
    quotes: list[dict[str, Any]] = field(default_factory=list)
    assets: dict[int, list[dict[str, Any]]] = field(default_factory=dict)


# --- Normalisation -----------------------------------------------------------


def is_blank(value: Any) -> bool:
    """True for ``None``, an empty container, or a string of only whitespace.

    Non-breaking and other Unicode spaces count as whitespace.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return not value.replace("\xa0", " ").strip()
    if isinstance(value, (list, dict, tuple, set)):
        return not value
    return False


def norm_text(value: Any) -> str:
    """Lower-case, accent-free, punctuation-free text with folded abbreviations.

    ``&`` becomes ``and``; every other non-alphanumeric run becomes one space.
    Digits are kept, so unit and street numbers stay distinct.
    """
    if is_blank(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ").replace("'", "")
    words = re.sub(r"[^a-z0-9]+", " ", text).split()
    return " ".join(WORD_FOLDS.get(word, word) for word in words)


def company_name_key(value: Any) -> str:
    """A company name for duplicate matching: legal-form suffixes dropped."""
    words = norm_text(value).split()
    while len(words) > 1 and words[-1] in LEGAL_SUFFIXES:
        words.pop()
    return " ".join(words)


def compact_postcode(value: Any) -> str:
    """Upper case with all whitespace removed; ``""`` when blank."""
    if is_blank(value):
        return ""
    return re.sub(r"\s+", "", str(value).replace("\xa0", " ")).upper()


def is_uk_postcode(value: Any) -> bool:
    """True for a full UK postcode, in any case and with any spacing."""
    return UK_POSTCODE.fullmatch(compact_postcode(value)) is not None


def is_uk_country(value: Any) -> bool:
    """True when the country is blank (assumed UK) or names the UK."""
    if is_blank(value):
        return True
    return re.sub(r"[^a-z]", "", norm_text(value)) in UK_COUNTRIES


def norm_email(value: Any) -> str:
    """Lower-cased, trimmed email; ``""`` when blank."""
    return "" if is_blank(value) else str(value).strip().lower()


def norm_phone(value: Any) -> str:
    """Digits only, with a leading UK ``44`` (or ``44 (0)``) folded to ``0``.

    Returns ``""`` when there are too few digits to compare safely.
    """
    if is_blank(value):
        return ""
    digits = re.sub(r"\D", "", str(value))
    if digits.startswith("44") and len(digits) > 10:
        # "+44 113…" and "+44 (0)113…" both mean "0113…".
        digits = "0" + digits[2:].removeprefix("0")
    return digits if len(digits) >= MIN_PHONE_DIGITS else ""


def ref_id(value: Any) -> int | None:
    """The integer ``ID`` of a nested reference, or ``None``."""
    if isinstance(value, Mapping):
        ident = value.get("ID")
        if isinstance(ident, int) and not isinstance(ident, bool) and ident > 0:
            return ident
    return None


def ref_ids(values: Any) -> list[int]:
    """The distinct integer IDs in a list of references, in first-seen order."""
    if not isinstance(values, list):
        return []
    seen: dict[int, None] = {}
    for value in values:
        ident = ref_id(value)
        if ident is not None:
            seen[ident] = None
    return list(seen)


def is_archived(row: Row) -> bool:
    """True only when ``Archived`` is literally ``true``."""
    return row.get("Archived") is True


def address_of(row: Row) -> Mapping[str, Any]:
    """A row's ``Address`` block, or an empty mapping."""
    address = row.get("Address")
    return address if isinstance(address, Mapping) else {}


def address_key(row: Row) -> tuple[str, str] | None:
    """A site's address for duplicate matching, or ``None`` if too blank.

    The key is the normalised street line plus the compact postcode (or the
    city when there is no postcode). Two blank addresses never match, and a
    postcode alone is not enough, since many sites share one.
    """
    address = address_of(row)
    street = norm_text(address.get("Address"))
    place = compact_postcode(address.get("PostalCode")) or norm_text(
        address.get("City")
    )
    if not street or not place:
        return None
    return street, place


# --- Run hygiene -------------------------------------------------------------


def dedupe_by_id(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Drop rows whose ``ID`` was already seen; keep the first.

    Offset paging can shift when records change mid-run, so a row can appear
    on two pages. Returns the unique rows and the number dropped.
    """
    seen: set[Any] = set()
    unique = []
    dropped = 0
    for row in rows:
        ident = row.get("ID")
        if ident in seen:
            dropped += 1
            continue
        seen.add(ident)
        unique.append(row)
    return unique, dropped


def check_projection(
    rows: list[dict[str, Any]], fields: Iterable[str]
) -> dict[str, int]:
    """Check that each requested field came back.

    Raises :class:`ProjectionError` when a field is absent from **every** row,
    which means Simpro ignored it, so any check on it would report every row.
    Returns, per field, how many rows lack the key (Simpro may omit a key on
    some rows); those rows are treated as blank and counted in the summary.
    """
    fields = list(fields)
    if not rows:
        return dict.fromkeys(fields, 0)
    absent = {name: sum(1 for row in rows if name not in row) for name in fields}
    ignored = sorted(name for name, count in absent.items() if count == len(rows))
    if ignored:
        raise ProjectionError(f"fields absent from every row: {ignored}")
    return absent


# --- Grouping helpers --------------------------------------------------------


def _groups(check: str, members: list[set[int]]) -> dict[int, str]:
    """Number groups of two or more by smallest member ID: ``{id: group}``."""
    real = sorted(sorted(group) for group in members if len(group) > 1)
    labels = {}
    for number, group in enumerate(real, start=1):
        for ident in group:
            labels[ident] = f"{check}-{number:04d}"
    return labels


class _UnionFind:
    """Minimal union-find over integer IDs."""

    def __init__(self) -> None:
        self.parent: dict[int, int] = {}

    def find(self, item: int) -> int:
        self.parent.setdefault(item, item)
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, a: int, b: int) -> None:
        self.parent[self.find(a)] = self.find(b)

    def sets(self) -> list[set[int]]:
        out: dict[int, set[int]] = defaultdict(set)
        for item in self.parent:
            out[self.find(item)].add(item)
        return list(out.values())


# --- Record lookups ----------------------------------------------------------


def _customers(snap: Snapshot) -> dict[int, dict[str, Any]]:
    """Every customer by ID, with a ``_kind`` of ``company`` or ``individual``."""
    out: dict[int, dict[str, Any]] = {}
    for kind, rows in (
        ("company", snap.company_customers),
        ("individual", snap.individual_customers),
    ):
        for row in rows:
            out[row["ID"]] = {**row, "_kind": kind}
    return out


def customer_name(row: Row) -> str:
    """A customer's display name, from whichever name fields it has."""
    if not is_blank(row.get("CompanyName")):
        return str(row["CompanyName"]).strip()
    parts = [row.get("GivenName"), row.get("FamilyName")]
    return " ".join(str(part).strip() for part in parts if not is_blank(part))


def _site_fields(row: Row) -> dict[str, Any]:
    address = address_of(row)
    return {
        "name": row.get("Name"),
        "street": address.get("Address"),
        "city": address.get("City"),
        "postcode": address.get("PostalCode"),
        "country": address.get("Country"),
        "customer_ids": ";".join(map(str, ref_ids(row.get("Customers")))),
        "archived": is_archived(row),
    }


def _customer_fields(row: Row) -> dict[str, Any]:
    return {
        "kind": row.get("_kind", ""),
        "name": customer_name(row),
        "email": row.get("Email"),
        "phone": row.get("Phone"),
        "archived": is_archived(row),
    }


def _is_open_job(row: Row) -> bool:
    return row.get("Stage") in OPEN_JOB_STAGES


def _is_open_quote(row: Row) -> bool:
    return row.get("Stage") in OPEN_QUOTE_STAGES and row.get("IsClosed") is not True


def _work_by_site(snap: Snapshot) -> tuple[dict[int, int], dict[int, int]]:
    """Per site ID: how many jobs and quotes in total, and how many open."""
    total: dict[int, int] = defaultdict(int)
    open_: dict[int, int] = defaultdict(int)
    for rows, is_open in ((snap.jobs, _is_open_job), (snap.quotes, _is_open_quote)):
        for row in rows:
            site = ref_id(row.get("Site"))
            if site is None:
                continue
            total[site] += 1
            if is_open(row):
                open_[site] += 1
    return total, open_


# --- Site checks -------------------------------------------------------------


def check_s1_site_no_customer(snap: Snapshot) -> list[Finding]:
    """S1: sites with no customer."""
    return [
        Finding("S1", row["ID"], "no customer", _site_fields(row))
        for row in snap.sites
        if not ref_ids(row.get("Customers"))
    ]


def check_s2_site_bad_customer(snap: Snapshot) -> list[Finding]:
    """S2: sites linked to a customer that is missing or archived."""
    customers = _customers(snap)
    findings = []
    for row in snap.sites:
        for ident in ref_ids(row.get("Customers")):
            if ident not in customers:
                reason = f"customer {ident} not found"
            elif is_archived(customers[ident]):
                reason = f"customer {ident} archived"
            else:
                continue
            findings.append(Finding("S2", row["ID"], reason, _site_fields(row)))
    return findings


def check_s3a_site_exact_duplicates(snap: Snapshot) -> list[Finding]:
    """S3a: sites with the same normalised name and address."""
    by_key: dict[tuple[str, tuple[str, str]], set[int]] = defaultdict(set)
    rows = {row["ID"]: row for row in snap.sites}
    for row in snap.sites:
        name, addr = norm_text(row.get("Name")), address_key(row)
        if name and addr:
            by_key[(name, addr)].add(row["ID"])
    labels = _groups("S3a", list(by_key.values()))
    return [
        Finding("S3a", i, "same name and address", _site_fields(rows[i]), group)
        for i, group in labels.items()
    ]


def check_s3b_site_shared_address(snap: Snapshot) -> list[Finding]:
    """S3b: one normalised address carrying more than one site name."""
    by_addr: dict[tuple[str, str], set[int]] = defaultdict(set)
    rows = {row["ID"]: row for row in snap.sites}
    for row in snap.sites:
        addr = address_key(row)
        if addr:
            by_addr[addr].add(row["ID"])
    shared = [
        ids
        for ids in by_addr.values()
        if len({norm_text(rows[i].get("Name")) for i in ids}) > 1
    ]
    labels = _groups("S3b", shared)
    return [
        Finding("S3b", i, "same address, different names", _site_fields(rows[i]), g)
        for i, g in labels.items()
    ]


def _numbers(text: str) -> list[str]:
    return re.findall(r"\d+", text)


def similar_names(a: str, b: str) -> bool:
    """True when two normalised names are near-identical.

    Names must carry the same numbers ("12 High St" is not "14 High St") and
    reach :data:`FUZZY_RATIO`. Identical names count as similar.
    """
    if not a or not b or _numbers(a) != _numbers(b):
        return False
    if a == b:
        return True
    matcher = difflib.SequenceMatcher(None, a, b)
    return matcher.quick_ratio() >= FUZZY_RATIO and matcher.ratio() >= FUZZY_RATIO


def s3c_groups(sites: list[Row]) -> tuple[list[set[int]], int]:
    """Groups of sites with similar names at different addresses.

    Names are blocked by first word, so only names sharing it are compared.
    Blocks over :data:`FUZZY_BLOCK_LIMIT` are skipped and counted; identical
    names inside a skipped block are still grouped. Pairs at the same address
    key are left to S3a/S3b. Returns the groups and the skipped-block count.
    """
    union = _UnionFind()
    blocks: dict[str, list[Row]] = defaultdict(list)
    for row in sites:
        name = norm_text(row.get("Name"))
        if name:
            blocks[name.split()[0]].append(row)
    skipped = 0
    for block in blocks.values():
        if len(block) > FUZZY_BLOCK_LIMIT:
            skipped += 1
            pairs = _same_name_pairs(block)
        else:
            pairs = (
                (a, b)
                for n, a in enumerate(block)
                for b in block[n + 1 :]
                if similar_names(norm_text(a.get("Name")), norm_text(b.get("Name")))
            )
        for a, b in pairs:
            if address_key(a) is None or address_key(a) != address_key(b):
                union.union(a["ID"], b["ID"])
    return union.sets(), skipped


def _same_name_pairs(block: list[Row]) -> Iterable[tuple[Row, Row]]:
    by_name: dict[str, list[Row]] = defaultdict(list)
    for row in block:
        by_name[norm_text(row.get("Name"))].append(row)
    for rows in by_name.values():
        for n, a in enumerate(rows):
            for b in rows[n + 1 :]:
                yield a, b


def check_s3c_site_similar_names(snap: Snapshot) -> list[Finding]:
    """S3c: similar site names at different (or blank) addresses."""
    rows = {row["ID"]: row for row in snap.sites}
    groups, _ = s3c_groups(snap.sites)
    labels = _groups("S3c", groups)
    return [
        Finding("S3c", i, "similar name, different address", _site_fields(rows[i]), g)
        for i, g in labels.items()
    ]


def check_s4_site_no_assets(snap: Snapshot) -> list[Finding]:
    """S4: sites with no assets. A site that was not scanned is an error."""
    unscanned = [row["ID"] for row in snap.sites if row["ID"] not in snap.assets]
    if unscanned:
        raise ProjectionError(f"{len(unscanned)} sites were not scanned for assets")
    return [
        Finding("S4", row["ID"], "no assets", _site_fields(row))
        for row in snap.sites
        if not snap.assets[row["ID"]]
    ]


def check_s5a_site_incomplete_address(snap: Snapshot) -> list[Finding]:
    """S5a: sites missing a street, city or postcode."""
    findings = []
    for row in snap.sites:
        address = address_of(row)
        missing = [
            label
            for key, label in (
                ("Address", "street"),
                ("City", "city"),
                ("PostalCode", "postcode"),
            )
            if is_blank(address.get(key))
        ]
        if missing:
            reason = "blank " + ", ".join(missing)
            findings.append(Finding("S5a", row["ID"], reason, _site_fields(row)))
    return findings


def check_s5b_site_bad_postcode(snap: Snapshot) -> list[Finding]:
    """S5b: UK sites whose postcode is present but not a valid UK postcode."""
    return [
        Finding("S5b", row["ID"], "invalid UK postcode", _site_fields(row))
        for row in snap.sites
        if is_uk_country(address_of(row).get("Country"))
        and not is_blank(address_of(row).get("PostalCode"))
        and not is_uk_postcode(address_of(row).get("PostalCode"))
    ]


def check_s5c_site_non_uk(snap: Snapshot) -> list[Finding]:
    """S5c: sites whose country is set and not the UK (postcode not checked)."""
    return [
        Finding("S5c", row["ID"], "country is not UK", _site_fields(row))
        for row in snap.sites
        if not is_uk_country(address_of(row).get("Country"))
    ]


def is_placeholder_name(value: Any) -> bool:
    """True for a blank name or one that says "not a real record"."""
    name = norm_text(value)
    return (
        not name
        or name in PLACEHOLDER_NAMES
        or any(name.startswith(prefix) for prefix in PLACEHOLDER_PREFIXES)
    )


def check_s6_site_placeholder_name(snap: Snapshot) -> list[Finding]:
    """S6: sites with a blank or placeholder name."""
    return [
        Finding("S6", row["ID"], "blank or placeholder name", _site_fields(row))
        for row in snap.sites
        if is_placeholder_name(row.get("Name"))
    ]


def check_s7_site_dormant(snap: Snapshot) -> list[Finding]:
    """S7: active sites that never had a job or a quote."""
    total, _ = _work_by_site(snap)
    return [
        Finding("S7", row["ID"], "no jobs or quotes ever", _site_fields(row))
        for row in snap.sites
        if not is_archived(row) and not total.get(row["ID"])
    ]


def check_s8_site_no_primary_contact(snap: Snapshot) -> list[Finding]:
    """S8: sites whose primary contact has no name and no email."""
    findings = []
    for row in snap.sites:
        contact = row.get("PrimaryContact")
        contact = contact if isinstance(contact, Mapping) else {}
        if all(is_blank(contact.get(k)) for k in ("GivenName", "FamilyName", "Email")):
            findings.append(
                Finding("S8", row["ID"], "no primary contact", _site_fields(row))
            )
    return findings


def check_s9_site_many_customers(snap: Snapshot) -> list[Finding]:
    """S9: sites with more than one customer (allowed; for review)."""
    return [
        Finding("S9", row["ID"], "more than one customer", _site_fields(row))
        for row in snap.sites
        if len(ref_ids(row.get("Customers"))) > 1
    ]


def check_s10_archived_site_open_work(snap: Snapshot) -> list[Finding]:
    """S10: archived sites with open jobs or quotes."""
    _, open_ = _work_by_site(snap)
    return [
        Finding(
            "S10",
            row["ID"],
            f"archived with {open_[row['ID']]} open jobs/quotes",
            _site_fields(row),
        )
        for row in snap.sites
        if is_archived(row) and open_.get(row["ID"])
    ]


# --- Customer checks ---------------------------------------------------------


def check_c1_customer_no_sites(snap: Snapshot) -> list[Finding]:
    """C1: customers with no sites (by their own list or any site's link)."""
    linked = {i for row in snap.sites for i in ref_ids(row.get("Customers"))}
    return [
        Finding("C1", i, "no sites", _customer_fields(row))
        for i, row in sorted(_customers(snap).items())
        if not ref_ids(row.get("Sites")) and i not in linked
    ]


def check_c2_customer_no_contacts(snap: Snapshot) -> list[Finding]:
    """C2: company customers with no contacts.

    Individuals are skipped: an individual customer is usually their own
    contact, so an empty list there is normal.
    """
    return [
        Finding("C2", row["ID"], "no contacts", _customer_fields(row))
        for row in snap.company_customers
        if not ref_ids(row.get("Contacts"))
    ]


def check_c3_customer_duplicates(snap: Snapshot) -> list[Finding]:
    """C3: duplicate customers.

    Companies match on name with legal-form suffixes dropped. Individuals match
    on full name plus a shared email or phone, since names alone collide.
    """
    customers = _customers(snap)
    union = _UnionFind()
    by_company: dict[str, list[int]] = defaultdict(list)
    for row in snap.company_customers:
        key = company_name_key(row.get("CompanyName"))
        if key:
            by_company[key].append(row["ID"])
    by_person: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in snap.individual_customers:
        name = norm_text(f"{row.get('GivenName') or ''} {row.get('FamilyName') or ''}")
        if not name:
            continue
        for contact in [norm_email(row.get("Email")), *_phones(row)]:
            if contact:
                by_person[(name, contact)].append(row["ID"])
    for ids in [*by_company.values(), *by_person.values()]:
        for other in ids[1:]:
            union.union(ids[0], other)
    labels = _groups("C3", union.sets())
    return [
        Finding("C3", i, "duplicate customer", _customer_fields(customers[i]), g)
        for i, g in labels.items()
    ]


def _phones(row: Row) -> list[str]:
    keys = ("Phone", "AltPhone", "CellPhone")
    return [p for p in dict.fromkeys(norm_phone(row.get(k)) for k in keys) if p]


def check_c4_customer_shared_contact_details(snap: Snapshot) -> list[Finding]:
    """C4: the same email or phone on different customers."""
    customers = _customers(snap)
    union = _UnionFind()
    by_value: dict[str, list[int]] = defaultdict(list)
    for ident, row in customers.items():
        values = [norm_email(row.get("Email")), *_phones(row)]
        for value in dict.fromkeys(v for v in values if v):
            by_value[value].append(ident)
    for ids in by_value.values():
        for other in ids[1:]:
            union.union(ids[0], other)
    labels = _groups("C4", union.sets())
    return [
        Finding(
            "C4",
            i,
            "email or phone shared with another customer",
            _customer_fields(customers[i]),
            g,
        )
        for i, g in labels.items()
    ]


def check_c5_customer_uncontactable(snap: Snapshot) -> list[Finding]:
    """C5: customers with no email and no phone."""
    return [
        Finding("C5", i, "no email and no phone", _customer_fields(row))
        for i, row in sorted(_customers(snap).items())
        if is_blank(row.get("Email"))
        and all(is_blank(row.get(k)) for k in ("Phone", "AltPhone", "CellPhone"))
    ]


def check_c6_customer_blank_name(snap: Snapshot) -> list[Finding]:
    """C6: customers missing a required name field."""
    findings = []
    for row in snap.company_customers:
        if is_blank(row.get("CompanyName")):
            findings.append(
                Finding("C6", row["ID"], "blank company name", _customer_fields(row))
            )
    for row in snap.individual_customers:
        blank = [k for k in ("GivenName", "FamilyName") if is_blank(row.get(k))]
        if blank:
            findings.append(
                Finding(
                    "C6",
                    row["ID"],
                    "blank " + ", ".join(blank),
                    _customer_fields({**row, "_kind": "individual"}),
                )
            )
    return findings


def email_problem(value: Any) -> str | None:
    """Why an email field is malformed, or ``None`` if it is fine or blank."""
    if is_blank(value):
        return None
    text = str(value).strip()
    if re.search(r"[;,]", text) or len(re.findall("@", text)) > 1:
        return "more than one address in the field"
    if not EMAIL.fullmatch(text):
        return "malformed email"
    return None


def check_c7_customer_bad_email(snap: Snapshot) -> list[Finding]:
    """C7: customers whose email field is malformed."""
    findings = []
    for i, row in sorted(_customers(snap).items()):
        problem = email_problem(row.get("Email"))
        if problem:
            findings.append(Finding("C7", i, problem, _customer_fields(row)))
    return findings


def check_c8_archived_customer_active_links(snap: Snapshot) -> list[Finding]:
    """C8: archived customers with active sites or open jobs or quotes."""
    customers = _customers(snap)
    active_sites: dict[int, int] = defaultdict(int)
    for row in snap.sites:
        if not is_archived(row):
            for ident in ref_ids(row.get("Customers")):
                active_sites[ident] += 1
    open_work: dict[int, int] = defaultdict(int)
    for rows, is_open in ((snap.jobs, _is_open_job), (snap.quotes, _is_open_quote)):
        for row in rows:
            ident = ref_id(row.get("Customer"))
            if ident is not None and is_open(row):
                open_work[ident] += 1
    findings = []
    for ident, row in sorted(customers.items()):
        sites, work = active_sites.get(ident, 0), open_work.get(ident, 0)
        if is_archived(row) and (sites or work):
            reason = f"archived with {sites} active sites, {work} open jobs/quotes"
            findings.append(Finding("C8", ident, reason, _customer_fields(row)))
    return findings


def check_c9_customer_list_consistency(snap: Snapshot) -> list[Finding]:
    """C9: the customer summary list and the two subtype lists disagree."""
    companies = {row["ID"] for row in snap.company_customers}
    individuals = {row["ID"] for row in snap.individual_customers}
    findings = [
        Finding("C9", i, "listed as both company and individual")
        for i in sorted(companies & individuals)
    ]
    findings += [
        Finding("C9", i, "in summary list, in neither subtype list")
        for i in sorted(snap.summary_customer_ids - companies - individuals)
    ]
    findings += [
        Finding("C9", i, "in a subtype list, not in summary list")
        for i in sorted((companies | individuals) - snap.summary_customer_ids)
    ]
    subtotal = len(companies | individuals)
    if snap.summary_customer_total != subtotal:
        findings.append(
            Finding(
                "C9",
                "totals",
                f"summary total {snap.summary_customer_total} != "
                f"companies + individuals {subtotal}",
            )
        )
    return findings


# --- Contact checks ----------------------------------------------------------


def _contact_rows(snap: Snapshot) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    for customer in snap.company_customers + snap.individual_customers:
        contacts = customer.get("Contacts")
        for contact in contacts if isinstance(contacts, list) else []:
            if isinstance(contact, Mapping) and ref_id(contact) is not None:
                yield customer, dict(contact)


def _contact_fields(customer: Row, contact: Row) -> dict[str, Any]:
    return {
        "customer_id": customer.get("ID"),
        "customer_name": customer_name(customer),
        "given_name": contact.get("GivenName"),
        "family_name": contact.get("FamilyName"),
        "email": contact.get("Email"),
    }


def check_ct1_contact_duplicates(snap: Snapshot) -> list[Finding]:
    """CT1: contacts duplicated within one customer (same name or email)."""
    findings = []
    for customer in snap.company_customers + snap.individual_customers:
        union = _UnionFind()
        keyed: dict[str, list[int]] = defaultdict(list)
        contacts = {}
        for owner, contact in _contact_rows(Snapshot(company_customers=[customer])):
            contacts[contact["ID"]] = (owner, contact)
            name = norm_text(
                f"{contact.get('GivenName') or ''} {contact.get('FamilyName') or ''}"
            )
            for key in (
                f"n:{name}" if name else "",
                f"e:{norm_email(contact.get('Email'))}",
            ):
                if key and key != "e:":
                    keyed[key].append(contact["ID"])
        for ids in keyed.values():
            for other in ids[1:]:
                union.union(ids[0], other)
        prefix = f"CT1-{customer['ID']}"
        for i, label in _groups(prefix, union.sets()).items():
            owner, contact = contacts[i]
            findings.append(
                Finding(
                    "CT1",
                    i,
                    "duplicate contact on one customer",
                    _contact_fields(owner, contact),
                    label,
                )
            )
    return findings


def check_ct2_contact_blank_name(snap: Snapshot) -> list[Finding]:
    """CT2: contacts with neither a given nor a family name."""
    return [
        Finding("CT2", contact["ID"], "blank name", _contact_fields(owner, contact))
        for owner, contact in _contact_rows(snap)
        if is_blank(contact.get("GivenName")) and is_blank(contact.get("FamilyName"))
    ]


# --- Asset checks ------------------------------------------------------------


def check_a1_asset_bad_parent(snap: Snapshot) -> list[Finding]:
    """A1: assets whose parent is not an asset on the same site."""
    findings = []
    for site_id, assets in sorted(snap.assets.items()):
        ids = {asset.get("ID") for asset in assets}
        for asset in assets:
            parent = asset.get("ParentID")
            if parent == asset.get("ID"):
                reason = "asset is its own parent"
            elif parent in (None, 0) or parent in ids:
                continue
            else:
                reason = f"parent {parent} not on this site"
            findings.append(Finding("A1", asset["ID"], reason, {"site_id": site_id}))
    return findings


def check_a2_asset_on_archived_site(snap: Snapshot) -> list[Finding]:
    """A2: active assets on an archived site."""
    archived = {row["ID"]: row for row in snap.sites if is_archived(row)}
    return [
        Finding(
            "A2",
            asset["ID"],
            "active asset on archived site",
            {"site_id": site_id, "site_name": archived[site_id].get("Name")},
        )
        for site_id, assets in sorted(snap.assets.items())
        if site_id in archived
        for asset in assets
        if not is_archived(asset)
    ]


# --- Job and quote checks ----------------------------------------------------


def _work_fields(row: Row) -> dict[str, Any]:
    return {
        "company": row.get("_company", ""),
        "stage": row.get("Stage"),
        "site_id": ref_id(row.get("Site")),
        "customer_id": ref_id(row.get("Customer")),
    }


def _check_work_links(check: str, rows: list[dict[str, Any]], snap: Snapshot):
    sites = {row["ID"] for row in snap.sites}
    customers = _customers(snap)
    findings = []
    for row in rows:
        site, customer = ref_id(row.get("Site")), ref_id(row.get("Customer"))
        problems = []
        if site is None:
            problems.append("no site")
        elif site not in sites:
            problems.append(f"site {site} not found")
        if customer is None:
            problems.append("no customer")
        elif customer not in customers:
            problems.append(f"customer {customer} not found")
        if problems:
            findings.append(
                Finding(check, row["ID"], "; ".join(problems), _work_fields(row))
            )
    return findings


def _check_work_customer_on_site(
    check: str, rows: list[dict[str, Any]], snap: Snapshot
) -> list[Finding]:
    site_customers = {
        row["ID"]: set(ref_ids(row.get("Customers"))) for row in snap.sites
    }
    findings = []
    for row in rows:
        site, customer = ref_id(row.get("Site")), ref_id(row.get("Customer"))
        if (
            site in site_customers
            and customer is not None
            and customer not in site_customers[site]
        ):
            findings.append(
                Finding(
                    check,
                    row["ID"],
                    "customer is not one of the site's customers",
                    _work_fields(row),
                )
            )
    return findings


def check_j1_job_links(snap: Snapshot) -> list[Finding]:
    """J1: jobs with no site or customer, or one that does not exist."""
    return _check_work_links("J1", snap.jobs, snap)


def check_q1_quote_links(snap: Snapshot) -> list[Finding]:
    """Q1: quotes with no site or customer, or one that does not exist."""
    return _check_work_links("Q1", snap.quotes, snap)


def check_j2_job_customer_not_on_site(snap: Snapshot) -> list[Finding]:
    """J2: jobs whose customer is not one of their site's customers."""
    return _check_work_customer_on_site("J2", snap.jobs, snap)


def check_q2_quote_customer_not_on_site(snap: Snapshot) -> list[Finding]:
    """Q2: quotes whose customer is not one of their site's customers."""
    return _check_work_customer_on_site("Q2", snap.quotes, snap)


def check_x1_site_sets_differ(snap: Snapshot) -> list[Finding]:
    """X1: site IDs seen by one configured company and not the other."""
    service = {row["ID"] for row in snap.sites}
    other = snap.other_company_site_ids
    return [
        Finding("X1", i, "site only in the service company")
        for i in sorted(service - other)
    ] + [
        Finding("X1", i, "site only in the projects company")
        for i in sorted(other - service)
    ]


#: Every check, by ID, in report order.
CHECKS: dict[str, Callable[[Snapshot], list[Finding]]] = {
    "S1": check_s1_site_no_customer,
    "S2": check_s2_site_bad_customer,
    "S3a": check_s3a_site_exact_duplicates,
    "S3b": check_s3b_site_shared_address,
    "S3c": check_s3c_site_similar_names,
    "S4": check_s4_site_no_assets,
    "S5a": check_s5a_site_incomplete_address,
    "S5b": check_s5b_site_bad_postcode,
    "S5c": check_s5c_site_non_uk,
    "S6": check_s6_site_placeholder_name,
    "S7": check_s7_site_dormant,
    "S8": check_s8_site_no_primary_contact,
    "S9": check_s9_site_many_customers,
    "S10": check_s10_archived_site_open_work,
    "C1": check_c1_customer_no_sites,
    "C2": check_c2_customer_no_contacts,
    "C3": check_c3_customer_duplicates,
    "C4": check_c4_customer_shared_contact_details,
    "C5": check_c5_customer_uncontactable,
    "C6": check_c6_customer_blank_name,
    "C7": check_c7_customer_bad_email,
    "C8": check_c8_archived_customer_active_links,
    "C9": check_c9_customer_list_consistency,
    "CT1": check_ct1_contact_duplicates,
    "CT2": check_ct2_contact_blank_name,
    "A1": check_a1_asset_bad_parent,
    "A2": check_a2_asset_on_archived_site,
    "J1": check_j1_job_links,
    "J2": check_j2_job_customer_not_on_site,
    "Q1": check_q1_quote_links,
    "Q2": check_q2_quote_customer_not_on_site,
    "X1": check_x1_site_sets_differ,
}


# --- Report ------------------------------------------------------------------


def safe_cell(value: Any) -> str:
    """A CSV cell that a spreadsheet will not run as a formula.

    Simpro text is typed by people; a leading ``=``, ``+``, ``-`` or ``@``
    would make Excel evaluate it when Alex opens the report.
    """
    if value is None:
        return ""
    text = str(value)
    return "'" + text if text.startswith(FORMULA_PREFIXES) else text


def ensure_git_ignored(path: Path) -> None:
    """Raise unless git ignores ``path``, so the report can never be committed.

    Uses ``git check-ignore`` from the path's nearest existing parent, so it
    works before the report directory exists.
    """
    probe = path / "probe.csv"
    cwd = next(p for p in [path, *path.parents] if p.exists())
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(probe)],
        cwd=cwd,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("report directory is not git-ignored; refusing to write")


class ReportWriter:
    """Writes one audit run's CSVs and ``summary.md`` to a private directory.

    The directory is created 0700 and each file 0600. The summary starts out
    ``INCOMPLETE`` and says ``COMPLETE`` only after :meth:`finish`, so a run
    that dies partway is never mistaken for a clean one.
    """

    def __init__(self, directory: Path) -> None:
        ensure_git_ignored(directory)
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(directory, 0o700)
        self.directory = directory
        self.counts: dict[str, int | str] = {}
        self.notes: list[str] = []
        self.complete = False
        self.write_summary()

    def _open(self, name: str):
        path = self.directory / name
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.chmod(path, 0o600)
        return os.fdopen(fd, "w", newline="", encoding="utf-8")

    def write_check(self, check: str, findings: list[Finding]) -> None:
        """Write ``<check>.csv``, sorted by group then record ID."""
        extra: dict[str, None] = {}
        for finding in findings:
            extra.update(dict.fromkeys(finding.fields))
        header = ["check", "group", "record_id", "reason", *extra]
        ordered = sorted(findings, key=lambda f: (f.group, str(f.record_id).zfill(12)))
        with self._open(f"{check}.csv") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            for f in ordered:
                writer.writerow(
                    [
                        safe_cell(v)
                        for v in [
                            f.check,
                            f.group,
                            f.record_id,
                            f.reason,
                            *(f.fields.get(k) for k in extra),
                        ]
                    ]
                )
        self.counts[check] = len(findings)
        self.write_summary()

    def record_error(self, check: str, message: str) -> None:
        """Record that a check could not run (message holds no values)."""
        self.counts[check] = f"ERROR: {message}"
        self.write_summary()

    def note(self, line: str) -> None:
        """Add a line about the run (totals, drift, requests) to the summary."""
        self.notes.append(line)
        self.write_summary()

    def finish(self, expected: Iterable[str]) -> None:
        """Mark the run complete if every expected check ran without error.

        A check that never ran (deselected, or the run died first) keeps the
        summary ``INCOMPLETE``, as does any check that recorded an error.
        """
        ran = {k for k, v in self.counts.items() if isinstance(v, int)}
        self.complete = set(expected) <= ran and len(ran) == len(self.counts)
        self.write_summary()

    def write_summary(self) -> None:
        """Rewrite ``summary.md`` from the current state."""
        state = "COMPLETE" if self.complete else "INCOMPLETE"
        lines = [f"# Simpro data-quality audit: {state}", "", "## Run", ""]
        lines += [f"- {note}" for note in self.notes]
        lines += ["", "## Findings per check", "", "| Check | Findings |", "|---|---|"]
        lines += [f"| {check} | {count} |" for check, count in self.counts.items()]
        with self._open("summary.md") as handle:
            handle.write("\n".join(lines) + "\n")
