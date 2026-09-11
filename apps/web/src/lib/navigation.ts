/**
 * The single navigation registry.
 *
 * The sidebar and the global search dialog both read this module, so a label,
 * a permission gate or a feature flag cannot be changed in one and drift in
 * the other. It holds no React state; `useEnabledNavItems` applies the
 * per-session gates.
 */

import {
  Activity,
  BarChart3,
  Briefcase,
  Building2,
  Calendar,
  ClipboardCheck,
  FileSignature,
  FolderOpen,
  Handshake,
  Headphones,
  HeartPulse,
  Home,
  MessageSquare,
  PhoneCall,
  ShieldCheck,
  Stethoscope,
  Tag,
  UserCog,
  UserRound,
  Users,
} from "lucide-react"

import { type FeatureFlag, featureFlags } from "@/lib/featureFlags"

export type NavItem = {
  to: string
  label: string
  icon: React.ElementType
  iconClassName?: string
  flag?: FeatureFlag
  /** Rendered greyed out and non-navigable until the flag is on. */
  comingSoon?: FeatureFlag
  platformAdmin?: boolean
  /** Requires the Clinical access scope, hidden entirely otherwise (privacy wall). */
  clinicalScope?: boolean
  /**
   * Extra path prefixes that also count as this item being active, for a
   * module whose pages live under more than one route family. Defaults to
   * `[to]`.
   */
  matchPrefixes?: readonly string[]
  /**
   * Words that should also find this destination in search. Navigation
   * synonyms only: they route a search term to a page and say nothing about
   * how the underlying records relate.
   */
  aliases?: readonly string[]
}

/** Quick-access items: always visible at the top, no label. */
export const TOP_ITEMS: ReadonlyArray<NavItem> = [
  { to: "/", label: "Home", icon: Home, aliases: ["dashboard", "overview"] },
]

/** Day-to-day operational navigation: flat, no section label. */
export const MAIN_ITEMS: ReadonlyArray<NavItem> = [
  { to: "/clients", label: "Clients", icon: Building2, aliases: ["employers", "companies"] },
  { to: "/members", label: "Members", icon: Users, aliases: ["employees", "beneficiaries"] },
  { to: "/contacts", label: "Contacts", icon: Users, flag: "contacts" },
  {
    to: "/providers",
    label: "Providers",
    icon: UserRound,
    matchPrefixes: ["/providers", "/provider-organisations", "/provider-aliases"],
    aliases: ["practitioners", "therapists", "counsellors", "organisations"],
  },
  {
    to: "/service-sessions",
    label: "Sessions",
    icon: Calendar,
    aliases: ["appointments", "bookings"],
  },
  { to: "/cases", label: "Cases", icon: HeartPulse, clinicalScope: true },
  { to: "/care-callbacks", label: "Campaigns", icon: PhoneCall, comingSoon: "campaigns" },
  {
    to: "/care-callbacks/worklist",
    label: "My Worklist",
    icon: Headphones,
    comingSoon: "worklist",
  },
  { to: "/surveys", label: "Surveys", icon: MessageSquare, comingSoon: "surveys" },
  { to: "/engagements", label: "Engagements", icon: Handshake, comingSoon: "engagements" },
  { to: "/contracts", label: "Contracts", icon: FileSignature, aliases: ["agreements"] },
  { to: "/services", label: "Services", icon: Briefcase },
  { to: "/kpis", label: "KPIs", icon: BarChart3, flag: "kpis" },
  { to: "/documents", label: "Documents", icon: FolderOpen, flag: "documents" },
]

/** Configuration & admin: shown under a "Settings" label. */
export const SETTINGS_ITEMS: ReadonlyArray<NavItem> = [
  { to: "/industries", label: "Industries", icon: BarChart3 },
  { to: "/diagnoses", label: "Diagnoses", icon: Stethoscope },
  { to: "/tags", label: "Tags", icon: Tag },
  { to: "/users", label: "Platform Users", icon: UserCog, aliases: ["accounts", "staff"] },
  { to: "/audit", label: "Audits", icon: ClipboardCheck, flag: "audit" },
  { to: "/activities", label: "Activity Logs", icon: Activity, flag: "activities" },
  {
    to: "/tenants",
    label: "Tenants",
    icon: ShieldCheck,
    platformAdmin: true,
    aliases: ["workspaces"],
  },
]

export function isItemEnabled(
  item: NavItem,
  isPlatformAdmin: boolean,
  hasClinicalScope: boolean,
): boolean {
  if (item.flag && !featureFlags[item.flag]) return false
  // Server-derived, not read from VITE_PLATFORM_TENANT_ID: the old check
  // skipped itself when that variable was unset, so every tenant saw the link
  // and got a 403 on using it.
  if (item.platformAdmin && !isPlatformAdmin) return false
  if (item.clinicalScope && !hasClinicalScope) return false
  return true
}

export function isComingSoon(item: NavItem): boolean {
  return !!item.comingSoon && !featureFlags[item.comingSoon]
}

/**
 * Won't prefix-match when another nav item is an exact match for the current
 * path. Prevents /care-callbacks being active while on /care-callbacks/worklist.
 */
export function matchesPrefix(pathname: string, to: string, allTos: readonly string[]): boolean {
  if (to === "/") return pathname === "/"
  if (pathname === to) return true
  if (allTos.some((p) => p !== to && p === pathname)) return false
  return pathname.startsWith(to + "/")
}

/** An item is active if the path matches its own route or any extra prefix it owns. */
export function resolveActive(pathname: string, item: NavItem, allTos: readonly string[]): boolean {
  const prefixes = item.matchPrefixes ?? [item.to]
  return prefixes.some((to) => matchesPrefix(pathname, to, allTos))
}

/** Every path any of these items claims, for `matchesPrefix` exactness checks. */
export function navPrefixes(items: ReadonlyArray<NavItem>): string[] {
  return items.flatMap((item) => item.matchPrefixes ?? [item.to])
}

/** Whether a nav item's label or one of its aliases matches a typed query. */
export function matchesNavQuery(item: NavItem, query: string): boolean {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  if (item.label.toLowerCase().includes(needle)) return true
  return (item.aliases ?? []).some((alias) => alias.includes(needle))
}
