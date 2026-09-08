/**
 * Display helpers: single source of truth for how entities are rendered as
 * strings in the UI. Add new helpers here rather than inlining `${a} ${b}` in
 * components, so display drift between routes is eliminated.
 */

import { formatDay } from "@/lib/format"
import type { Contract, Member, Person, User } from "@/types/entities"

export function contractLabel(contract: Contract): string {
  return `${formatDay(contract.period.start_date)} to ${formatDay(contract.period.end_date)}`
}

/** The contract's own rate, e.g. "UGX 172,000,000". */
export function contractValue(contract: Contract): string {
  const parsed = Number(contract.billing_rate.amount)
  const amount = Number.isFinite(parsed) ? parsed.toLocaleString() : contract.billing_rate.amount
  return `${contract.billing_rate.currency} ${amount}`
}

/** A money amount on the wire, e.g. "UGX 7,200,000". Decimal strings stay exact. */
export function moneyLabel(money: { amount: string; currency: string }): string {
  const parsed = Number(money.amount)
  return `${money.currency} ${Number.isFinite(parsed) ? parsed.toLocaleString() : money.amount}`
}

export function memberLabel(member: Member): string {
  return member.display_label?.trim() || member.employer_member_id
}

/**
 * Display name for a Person.
 *
 * BE Person carries no name fields (per `PersonResponse` in `openapi.json`).
 * Identity comes from the linked `User.email`. This helper returns, in order
 * of preference:
 *   1. The legacy `first_name + last_name` if present (will disappear once
 *      backend dataset has all-fixture rows replaced).
 *   2. The linked user's email local-part (humanised).
 *   3. The User's full email.
 *   4. A short form of the Person id.
 */
export function displayName(person: Person, user?: User | null): string {
  const legacy =
    person.first_name || person.last_name
      ? `${person.first_name ?? ""} ${person.last_name ?? ""}`.trim()
      : ""
  if (legacy) return legacy
  if (user?.display_name) return user.display_name
  if (user?.email) {
    const localPart = user.email.split("@")[0]
    return localPart
      ? localPart.replace(/[._-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
      : user.email
  }
  return person.id.slice(0, 8)
}

/** Initials for any display name, used in avatar placeholders. */
export function nameInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  if (parts[0]?.length >= 2) return parts[0].slice(0, 2).toUpperCase()
  return parts[0]?.[0]?.toUpperCase() ?? "·"
}

/**
 * Initials for a Person, used in avatar placeholders.
 */
export function personInitials(person: Person, user?: User | null): string {
  return nameInitials(displayName(person, user))
}

/**
 * Title-cases a stored name for display. Tenant names are stored as entered,
 * which is often all upper or all lower case.
 */
export function toProperCase(value: string): string {
  return value
    .split(/\s+/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ")
}

/**
 * A person-shaped label for an account.
 *
 * Prefers the account's own display name. When there isn't one, builds a label
 * from the email's local part rather than showing the raw address: the nav menu
 * shows who you are, not how you sign in. The label is derived, not asserted
 * identity, so the full email stays visible inside the account menu.
 */
export function accountDisplayName(
  displayName: string | null | undefined,
  email: string | null | undefined,
): string | null {
  const owned = displayName?.trim()
  if (owned) return owned
  const local = email?.split("@")[0]?.trim()
  if (!local) return null
  const words = local
    .split(/[._\-+]+/)
    .filter((part) => part && !/^\d+$/.test(part))
    .map(toProperCase)
  return words.length > 0 ? words.join(" ") : null
}
