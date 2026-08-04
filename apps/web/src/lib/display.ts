/**
 * Display helpers — single source of truth for how entities are rendered as
 * strings in the UI. Add new helpers here rather than inlining `${a} ${b}` in
 * components, so display drift between routes is eliminated.
 */

import type { Person, User } from '@/types/entities'

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
      ? `${person.first_name ?? ''} ${person.last_name ?? ''}`.trim()
      : ''
  if (legacy) return legacy
  if (user?.display_name) return user.display_name
  if (user?.email) {
    const localPart = user.email.split('@')[0]
    return localPart
      ? localPart.replace(/[._-]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
      : user.email
  }
  return person.id.slice(0, 8)
}

/** Initials for any display name, used in avatar placeholders. */
export function nameInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  if (parts[0]?.length >= 2) return parts[0].slice(0, 2).toUpperCase()
  return parts[0]?.[0]?.toUpperCase() ?? '·'
}

/**
 * Initials for a Person, used in avatar placeholders.
 */
export function personInitials(person: Person, user?: User | null): string {
  return nameInitials(displayName(person, user))
}
