"""Client CSV import pipeline.

Validation, reference resolution, and creation for both the synchronous
import route and the queued background job. The route layer owns HTTP
concerns and the request transaction; this module owns the import logic.
"""

from __future__ import annotations

import difflib
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field, replace

from app.application.use_cases.client_use_cases import CreateClientUseCase
from app.core.security import TokenData
from app.domain.entities.client import ClientEntity
from app.domain.enums import ContactMethod
from app.domain.repositories.client_alias_repository import ClientAliasRepository
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.value_objects.core import (
    Address,
    ClientId,
    ContactInfo,
    Email,
    IndustryId,
    TenantId,
)
from app.shared.utils.client_alias import normalize_client_alias
from app.shared.utils.client_csv import ClientCsvRow, Issue, generated_client_code
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

Decisions = dict[int, dict[str, str | None]]
ResolvedRow = tuple[ClientCsvRow, str, IndustryId | None, ClientId | None]

_MERGE_ACTIONS = {"create", "skip", "merge"}


@dataclass
class ImportRepositories:
    """The repositories the import pipeline writes through."""

    client: ClientRepository
    alias: ClientAliasRepository
    industry: IndustryRepository
    tenant: TenantRepository


@dataclass
class CreatedClient:
    name: str
    code: str


@dataclass
class ValidationResult:
    """Everything the pipeline learned before any row is written."""

    candidates: list[tuple[ClientCsvRow, str]] = field(default_factory=list)
    ready: list[ResolvedRow] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    matches: dict[int, ClientEntity] = field(default_factory=dict)
    similar_matches: dict[int, ClientEntity] = field(default_factory=dict)
    skipped: int = 0

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue["severity"] == "error"]

    @property
    def all_matches(self) -> dict[int, ClientEntity]:
        return {**self.matches, **self.similar_matches}


def issue(
    row: ClientCsvRow, field_name: str | None, message: str, severity: str = "error"
) -> Issue:
    return {
        "row": row.row_number,
        "field": field_name,
        "message": message,
        "severity": severity,
    }


def parse_decisions(raw: str | None, issues: list[Issue]) -> Decisions | None:
    """Decode row actions posted by the confirmation step."""
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        issues.append(
            {
                "row": 0,
                "field": "decisions",
                "message": "Invalid import decisions",
                "severity": "error",
            }
        )
        return {}
    if not isinstance(payload, dict):
        issues.append(
            {
                "row": 0,
                "field": "decisions",
                "message": "Invalid import decisions",
                "severity": "error",
            }
        )
        return {}

    decisions: Decisions = {}
    for key, value in payload.items():
        try:
            row_number = int(key)
        except (TypeError, ValueError):
            issues.append(
                {
                    "row": 0,
                    "field": "decisions",
                    "message": "Invalid row decision",
                    "severity": "error",
                }
            )
            continue
        if not isinstance(value, dict) or value.get("action") not in _MERGE_ACTIONS:
            issues.append(
                {
                    "row": row_number,
                    "field": "decisions",
                    "message": "Action must be create, skip, or merge",
                }
            )
            continue
        client_id = value.get("client_id")
        decisions[row_number] = {
            "action": str(value["action"]),
            "client_id": str(client_id) if client_id else None,
        }
    return decisions


def _valid_contact_method(row: ClientCsvRow) -> bool:
    if row.preferred_contact_method is None:
        return True
    try:
        ContactMethod(row.preferred_contact_method.lower())
    except ValueError:
        return False
    return True


def _valid_client_code(code: str) -> bool:
    return 3 <= len(code) <= 5 and code.isalnum()


def _missing_billing_fields(row: ClientCsvRow) -> str | None:
    """Name the fields an Address needs but the row omitted."""
    if not row.billing_street:
        return None
    missing = [
        label
        for label, value in (("city", row.billing_city), ("country", row.billing_country))
        if not value
    ]
    return " and ".join(missing) if missing else None


def _merge_duplicate_aliases(
    candidates: list[tuple[ClientCsvRow, str]], row: ClientCsvRow, name_key: str
) -> None:
    """Fold a duplicate row's aliases into the candidate that kept the name."""
    for index, (candidate, code) in enumerate(candidates):
        if candidate.name.casefold() == name_key:
            merged = tuple(dict.fromkeys(candidate.aliases + row.aliases))
            candidates[index] = (replace(candidate, aliases=merged), code)
            return


def prepare_rows(
    rows: list[ClientCsvRow], issues: list[Issue]
) -> tuple[list[tuple[ClientCsvRow, str]], int]:
    """Validate row-local fields and collapse duplicate names."""
    seen_names: set[str] = set()
    used_codes: set[str] = set()
    candidates: list[tuple[ClientCsvRow, str]] = []
    skipped = 0

    for row in rows:
        name_key = row.name.casefold()
        if name_key in seen_names:
            issues.append(issue(row, "name", "Duplicate name in file; skipped", "skipped"))
            _merge_duplicate_aliases(candidates, row, name_key)
            skipped += 1
            continue
        seen_names.add(name_key)

        if row.preferred_contact_method and not _valid_contact_method(row):
            issues.append(
                issue(
                    row,
                    "preferred_contact_method",
                    "Must be email, phone, sms, whatsapp, or wechat",
                )
            )
            continue

        missing = _missing_billing_fields(row)
        if missing:
            issues.append(issue(row, "billing_street", f"Billing address also requires {missing}"))
            continue

        # generated_client_code reserves the code it returns, so only a code
        # the CSV supplied can collide with one already used.
        if row.code:
            code = row.code.upper()
            if not _valid_client_code(code):
                issues.append(issue(row, "code", "Must be 3-5 alphanumeric characters"))
                continue
            if code in used_codes:
                issues.append(issue(row, "code", f"Duplicate code '{code}' in file"))
                continue
            used_codes.add(code)
        else:
            code = generated_client_code(row.name, used_codes)
        candidates.append((row, code))
    return candidates, skipped


def validate_file_aliases(candidates: list[tuple[ClientCsvRow, str]], issues: list[Issue]) -> None:
    """Reject aliases that collide with another row before any writes begin."""
    canonical_names = {normalize_client_alias(row.name): row for row, _ in candidates}
    owners: dict[str, ClientCsvRow] = {}
    for row, _ in candidates:
        for alias in row.aliases:
            normalized = normalize_client_alias(alias)
            if normalized in canonical_names and canonical_names[normalized] is not row:
                issues.append(
                    issue(
                        row,
                        "aliases",
                        f"Alias '{alias}' conflicts with another row's canonical name",
                    )
                )
            previous = owners.get(normalized)
            if previous is not None and previous is not row:
                issues.append(issue(row, "aliases", f"Alias '{alias}' is repeated for another row"))
            owners[normalized] = row


async def _alias_conflicts(
    row: ClientCsvRow,
    tenant_id: TenantId,
    repos: ImportRepositories,
    issues: list[Issue],
) -> bool:
    conflict = False
    for alias in row.aliases:
        owner = await repos.alias.find_by_normalized(tenant_id, normalize_client_alias(alias))
        canonical_owner = await repos.client.get_by_name(tenant_id, alias)
        if owner or canonical_owner:
            owner_name = canonical_owner.name if canonical_owner else "another client"
            issues.append(
                issue(
                    row,
                    "aliases",
                    f"Alias '{alias}' conflicts with {owner_name}; resolve before importing",
                )
            )
            conflict = True
    return conflict


def _existing_client_issue(row: ClientCsvRow, existing: ClientEntity) -> Issue:
    if existing.name.casefold() == row.name.casefold():
        detail = "Client name or alias already exists; skipped"
    else:
        detail = f"Matches existing client '{existing.name}' through its name or alias; skipped"
    return issue(row, "name", detail, "skipped")


async def remove_existing_rows(
    candidates: list[tuple[ClientCsvRow, str]],
    tenant_id: TenantId,
    repos: ImportRepositories,
    issues: list[Issue],
    decisions: Decisions | None,
    matches: dict[int, ClientEntity],
) -> tuple[list[tuple[ClientCsvRow, str]], int]:
    """Apply existing-client decisions and reject remaining tenant conflicts."""
    ready: list[tuple[ClientCsvRow, str]] = []
    skipped = 0

    for row, code in candidates:
        existing = await repos.client.get_by_name_or_alias(tenant_id, row.name)
        if existing:
            matches[row.row_number] = existing
            action = (decisions or {}).get(row.row_number, {}).get("action", "skip")
            if action == "merge":
                ready.append((row, code))
            elif action == "create":
                issues.append(issue(row, "name", "Client already exists; choose skip or merge"))
            else:
                issues.append(_existing_client_issue(row, existing))
                skipped += 1
            continue

        if await repos.client.get_by_code(tenant_id, code):
            issues.append(issue(row, "code", f"Client code '{code}' already exists"))
            continue
        if await _alias_conflicts(row, tenant_id, repos, issues):
            continue

        decision = (decisions or {}).get(row.row_number, {})
        if decision.get("action") == "skip":
            issues.append(issue(row, "name", "Skipped by user", "skipped"))
            skipped += 1
            continue
        if decision.get("action") == "merge" and not decision.get("client_id"):
            issues.append(issue(row, "name", "Choose a client before merging this row"))
            continue
        ready.append((row, code))
    return ready, skipped


async def add_similarity_warnings(
    rows: list[tuple[ClientCsvRow, str]],
    tenant_id: TenantId,
    repos: ImportRepositories,
    issues: list[Issue],
    similar_matches: dict[int, ClientEntity],
) -> None:
    """Flag close names for review without blocking a valid import."""
    existing = await repos.client.list_all(tenant_id, limit=10_000, include_archived=True)
    existing_names = {client.name.casefold(): client.name for client in existing}

    for row, _code in rows:
        close = difflib.get_close_matches(row.name.casefold(), existing_names, n=1, cutoff=0.86)
        if not close or close[0] == row.name.casefold():
            continue
        matched = next(client for client in existing if client.name.casefold() == close[0])
        similar_matches[row.row_number] = matched
        issues.append(
            issue(
                row,
                "name",
                f"Similar existing client: '{existing_names[close[0]]}'. Review before importing.",
                "warning",
            )
        )


async def resolve_references(
    rows: list[tuple[ClientCsvRow, str]],
    tenant_id: TenantId,
    repos: ImportRepositories,
    issues: list[Issue],
) -> list[ResolvedRow]:
    """Resolve optional human-readable industry and parent-client references."""
    resolved: list[ResolvedRow] = []
    for row, code in rows:
        industry_id = IndustryId(row.industry_id) if row.industry_id else None
        if row.industry:
            industry = await repos.industry.get_by_name(row.industry, tenant_id)
            if not industry:
                issues.append(issue(row, "industry", f"Industry '{row.industry}' not found"))
                continue
            industry_id = industry.id

        parent_client_id = ClientId(row.parent_client_id) if row.parent_client_id else None
        if row.parent_client_name:
            parent = await repos.client.get_by_name(tenant_id, row.parent_client_name)
            if not parent:
                issues.append(
                    issue(
                        row,
                        "parent_client_name",
                        f"Parent client '{row.parent_client_name}' not found",
                    )
                )
                continue
            parent_client_id = parent.id
        resolved.append((row, code, industry_id, parent_client_id))
    return resolved


def _merge_target_id(
    row: ClientCsvRow, decisions: Decisions | None, matches: dict[int, ClientEntity]
) -> str | None:
    decision = (decisions or {}).get(row.row_number, {})
    if decision.get("client_id"):
        return decision["client_id"]
    matched = matches.get(row.row_number)
    return matched.id.value if matched else None


async def validate_merge_decisions(
    rows: list[tuple[ClientCsvRow, str]],
    tenant_id: TenantId,
    repos: ImportRepositories,
    decisions: Decisions | None,
    matches: dict[int, ClientEntity],
    issues: list[Issue],
) -> None:
    """Validate merge targets before a confirmation can create any rows."""
    for row, _code in rows:
        if (decisions or {}).get(row.row_number, {}).get("action") != "merge":
            continue
        target_id = _merge_target_id(row, decisions, matches)
        target = await repos.client.get_by_id(ClientId(target_id)) if target_id else None
        if not target or target.tenant_id != tenant_id:
            issues.append(issue(row, "name", "Merge target was not found"))


async def validate(
    rows: list[ClientCsvRow],
    tenant_id: TenantId,
    repos: ImportRepositories,
    decisions: Decisions | None,
    issues: list[Issue],
) -> ValidationResult:
    """Run every check the import performs before writing a single row."""
    result = ValidationResult(issues=issues)
    result.candidates, result.skipped = prepare_rows(rows, issues)
    validate_file_aliases(result.candidates, issues)

    ready, existing_skipped = await remove_existing_rows(
        result.candidates, tenant_id, repos, issues, decisions, result.matches
    )
    result.skipped += existing_skipped
    result.ready = await resolve_references(ready, tenant_id, repos, issues)
    await add_similarity_warnings(ready, tenant_id, repos, issues, result.similar_matches)
    await validate_merge_decisions(ready, tenant_id, repos, decisions, result.all_matches, issues)
    return result


def contact_info(row: ClientCsvRow) -> ContactInfo:
    return ContactInfo(
        phone=row.phone,
        email=Email(row.email) if row.email else None,
        address=row.address,
    )


def billing_address(row: ClientCsvRow) -> Address | None:
    if not row.billing_street:
        return None
    return Address(
        street=row.billing_street,
        city=row.billing_city or "",
        country=row.billing_country or "",
        postal_code=row.billing_postal_code,
    )


async def _merge_into_existing(
    row: ClientCsvRow,
    tenant_id: TenantId,
    repos: ImportRepositories,
    target: ClientEntity,
    issues: list[Issue],
) -> bool:
    """Fold a row's aliases into an existing client. False when an alias clashes."""
    aliases = list(await repos.alias.list_for_client(target.id, tenant_id))
    alias_values = [alias.alias for alias in aliases]
    if normalize_client_alias(row.name) != normalize_client_alias(target.name):
        alias_values.append(row.name)
    alias_values.extend(row.aliases)

    for alias in alias_values:
        owner = await repos.alias.find_by_normalized(tenant_id, normalize_client_alias(alias))
        if owner and owner.client_id != target.id:
            issues.append(issue(row, "aliases", f"Alias '{alias}' belongs to another client"))
            return False
        canonical_owner = await repos.client.get_by_name(tenant_id, alias)
        if canonical_owner and canonical_owner.id != target.id:
            issues.append(issue(row, "aliases", f"Alias '{alias}' is another client's name"))
            return False

    merged = await repos.alias.replace_for_client(target.id, tenant_id, alias_values)
    target.aliases = [alias.alias for alias in merged]
    return True


async def create_clients(
    rows: list[ResolvedRow],
    tenant_id: TenantId,
    repos: ImportRepositories,
    current_user: TokenData,
    decisions: Decisions | None,
    matches: dict[int, ClientEntity],
    issues: list[Issue],
    audit_handler,
    request=None,
    progress_callback: Callable[[int], Awaitable[None]] | None = None,
) -> tuple[list[CreatedClient], int]:
    """Create and audit the prevalidated rows."""
    created: list[CreatedClient] = []
    failed = 0
    use_case = CreateClientUseCase(repos.client, repos.tenant, repos.industry)

    for index, (row, code, industry_id, parent_client_id) in enumerate(rows, start=1):
        if progress_callback is not None:
            await progress_callback(index)

        if (decisions or {}).get(row.row_number, {}).get("action") == "merge":
            target_id = _merge_target_id(row, decisions, matches)
            target = await repos.client.get_by_id(ClientId(target_id)) if target_id else None
            if not target or target.tenant_id != tenant_id:
                issues.append(issue(row, "name", "Merge target was not found"))
                failed += 1
                continue
            if not await _merge_into_existing(row, tenant_id, repos, target, issues):
                failed += 1
                continue
            await audit_change(target, audit_handler, current_user, request, tenant_id=tenant_id)
            created.append(CreatedClient(name=target.name, code=target.code))
            continue

        client = await use_case.execute(
            client_id=ClientId(generate_cuid()),
            tenant_id=tenant_id,
            name=row.name,
            code=code,
            contact_info=contact_info(row),
            billing_address=billing_address(row),
            industry_id=industry_id,
            parent_client_id=parent_client_id,
            preferred_contact_method=ContactMethod(row.preferred_contact_method.lower())
            if row.preferred_contact_method
            else None,
        )
        client.aliases = list(row.aliases)
        await repos.alias.replace_for_client(client.id, tenant_id, row.aliases)
        await audit_change(client, audit_handler, current_user, request, tenant_id=tenant_id)
        created.append(CreatedClient(name=client.name, code=client.code))
    return created, failed
