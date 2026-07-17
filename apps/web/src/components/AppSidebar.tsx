import { Link, useRouterState } from "@tanstack/react-router"
import {
  Activity,
  BarChart3,
  Briefcase,
  Building2,
  Calendar,
  ClipboardCheck,
  FileCheck,
  FileSignature,
  FolderOpen,
  Handshake,
  Headphones,
  Home,
  MessageSquare,
  PhoneCall,
  Search,
  ShieldCheck,
  Tag,
  UserCog,
  Users,
} from "lucide-react"

import { openCommandPalette } from "@/components/CommandPalette"
import { Button } from "@/components/ui/button"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { type FeatureFlag, featureFlags } from "@/lib/featureFlags"
import { cn } from "@/lib/utils"
import { useTenantStore } from "@/store/slices/tenantSlice"

const PROJECT_LOGO = "/evexi%CC%81a.svg"

type NavItem = {
  to: string
  label: string
  icon: React.ElementType
  iconClassName?: string
  flag?: FeatureFlag
  platformAdmin?: boolean
}

function platformTenantId(): string {
  return (import.meta.env.VITE_PLATFORM_TENANT_ID ?? "").trim()
}

/** Quick-access items — always visible at the top, no label. */
const TOP_ITEMS: ReadonlyArray<NavItem> = [
  { to: "/", label: "Home", icon: Home },
]

/** Day-to-day operational navigation — flat, no section label. */
const MAIN_ITEMS: ReadonlyArray<NavItem> = [
  { to: "/clients", label: "Clients", icon: Building2 },
  { to: "/persons", label: "Persons", icon: Users },
  { to: "/contacts", label: "Contacts", icon: Users, flag: "contacts" },
  { to: "/service-sessions", label: "Sessions", icon: Calendar },
  { to: "/care-callbacks", label: "Campaigns", icon: PhoneCall },
  { to: "/care-callbacks/worklist", label: "My Worklist", icon: Headphones },
  { to: "/surveys", label: "Surveys", icon: MessageSquare },
  { to: "/engagements", label: "Engagements", icon: Handshake },
  { to: "/contracts", label: "Contracts", icon: FileSignature },
  { to: "/service-assignments", label: "Assignments", icon: FileCheck },
  { to: "/services", label: "Services", icon: Briefcase },
  { to: "/kpis", label: "KPIs", icon: BarChart3, flag: "kpis" },
  { to: "/documents", label: "Documents", icon: FolderOpen, flag: "documents" },
]

/** Configuration & admin — shown under a "Settings" label. */
const SETTINGS_ITEMS: ReadonlyArray<NavItem> = [
  { to: "/industries", label: "Industries", icon: BarChart3 },
  { to: "/tags", label: "Tags", icon: Tag },
  { to: "/users", label: "Platform Users", icon: UserCog },
  { to: "/audit", label: "Audits", icon: ClipboardCheck, flag: "audit" },
  { to: "/activities", label: "Activity Logs", icon: Activity, flag: "activities" },
  { to: "/tenants", label: "Tenants", icon: ShieldCheck, platformAdmin: true },
]

function isItemEnabled(item: NavItem, currentTenantId: string | null): boolean {
  if (item.flag && !featureFlags[item.flag]) return false
  if (item.platformAdmin) {
    const required = platformTenantId()
    if (required && currentTenantId !== required) return false
  }
  return true
}

function toProperCase(s: string): string {
  return s
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ")
}

/**
 * Won't prefix-match when another nav item is an exact match for the current
 * path. Prevents /care-callbacks being active while on /care-callbacks/worklist.
 */
function resolveActive(pathname: string, to: string, allTos: readonly string[]): boolean {
  if (to === "/") return pathname === "/"
  if (pathname === to) return true
  if (allTos.some((p) => p !== to && p === pathname)) return false
  return pathname.startsWith(to + "/")
}

function useTenantDisplayName(): string {
  const currentTenant = useTenantStore((s) => s.currentTenant)
  return currentTenant?.name ? toProperCase(currentTenant.name) : "—"
}

// ─── Expanded sidebar ────────────────────────────────────────────────────────

function ExpandedHeader() {
  const displayName = useTenantDisplayName()
  return (
    <SidebarHeader className="gap-0 pb-2">
      <div className="flex h-11 items-center gap-2.5 px-2">
        <img src={PROJECT_LOGO} alt="" className="h-5 w-5 shrink-0 object-contain" />
        <span className="truncate text-sm font-semibold text-fg">{displayName}</span>
      </div>
      <div className="px-1">
        <Button
          type="button"
          variant="outline"
          onClick={openCommandPalette}
          aria-label="Search (⌘K)"
          aria-keyshortcuts="Meta+K Control+K"
          className="flex h-8 w-full cursor-pointer items-center justify-start gap-2 rounded-sm border-border bg-surface px-3 text-sm font-normal text-fg-subtle transition-colors hover:bg-surface-hover"
        >
          <Search className="size-3.5 shrink-0" aria-hidden />
          <span className="flex-1 text-left">Search</span>
          <kbd
            aria-hidden
            className="inline-flex h-5 select-none items-center rounded-sm border border-border bg-bg px-1.5 font-mono text-[10px] font-medium"
          >
            ⌘K
          </kbd>
        </Button>
      </div>
    </SidebarHeader>
  )
}

function NavItem({
  to,
  label,
  icon: Icon,
  iconClassName,
  isActive,
}: NavItem & { isActive: boolean }) {
  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={isActive}>
        <Link to={to}>
          <Icon className={iconClassName} />
          <span>{label}</span>
        </Link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  )
}

function ExpandedSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const currentTenantId = useTenantStore((s) => s.currentTenantId)

  const mainItems = MAIN_ITEMS.filter((i) => isItemEnabled(i, currentTenantId))
  const settingsItems = SETTINGS_ITEMS.filter((i) => isItemEnabled(i, currentTenantId))
  const allTos = [...TOP_ITEMS, ...mainItems, ...settingsItems].map((i) => i.to)
  const active = (to: string) => resolveActive(pathname, to, allTos)

  return (
    <>
      <ExpandedHeader />
      <SidebarContent className="gap-0 px-2 py-1">
        {/* Top shortcuts */}
        <SidebarGroup className="gap-0">
          <SidebarMenu>
            {TOP_ITEMS.map((item) => (
              <NavItem key={item.label} {...item} isActive={active(item.to)} />
            ))}
          </SidebarMenu>
        </SidebarGroup>

        {/* Main operational nav — flat, no label */}
        {mainItems.length > 0 && (
          <>
            <div className="mx-2 my-1 h-px bg-border" role="separator" />
            <SidebarGroup className="gap-0">
              <SidebarMenu>
                {mainItems.map((item) => (
                  <NavItem key={item.label} {...item} isActive={active(item.to)} />
                ))}
              </SidebarMenu>
            </SidebarGroup>
          </>
        )}

        {/* Settings / config */}
        {settingsItems.length > 0 && (
          <>
            <div className="mx-2 my-1 h-px bg-border" role="separator" />
            <SidebarGroup className="gap-0">
              <p className="px-2 pb-0.5 pt-1 text-[10px] font-medium tracking-widest text-fg-subtle/60">
                SETTINGS
              </p>
              <SidebarMenu>
                {settingsItems.map((item) => (
                  <NavItem key={item.label} {...item} isActive={active(item.to)} />
                ))}
              </SidebarMenu>
            </SidebarGroup>
          </>
        )}
      </SidebarContent>
    </>
  )
}

// ─── Collapsed sidebar ────────────────────────────────────────────────────────

const ICON_BTN =
  "relative grid h-7 w-7 mx-auto place-items-center rounded-sm text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring"

interface CollapsedNavLinkProps {
  to: string
  label: string
  icon: React.ElementType
  iconClassName?: string
  isActive: boolean
}

function CollapsedNavLink({ to, label, icon: Icon, iconClassName, isActive }: CollapsedNavLinkProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Link
          to={to}
          aria-label={label}
          aria-current={isActive ? "page" : undefined}
          className={cn(ICON_BTN, isActive && "bg-primary/10 text-primary")}
        >
          {isActive && (
            <span
              aria-hidden
              className="absolute left-0 top-1 bottom-1 w-0.5 rounded-r bg-primary"
            />
          )}
          <Icon className={cn("size-4", iconClassName)} />
        </Link>
      </TooltipTrigger>
      <TooltipContent side="right" className="font-medium">
        {label}
      </TooltipContent>
    </Tooltip>
  )
}

function CollapsedHeader() {
  const { setOpen } = useSidebar()
  const displayName = useTenantDisplayName()
  return (
    <SidebarHeader className="items-center gap-1 pb-2">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            aria-label={`${displayName} — expand sidebar`}
            onClick={() => setOpen(true)}
            className="mx-auto size-9 p-0 rounded-md hover:bg-sidebar-accent focus-visible:ring-sidebar-ring"
          >
            <img src={PROJECT_LOGO} alt="" className="h-5 w-5 object-contain" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="right" className="font-medium">
          {displayName}
        </TooltipContent>
      </Tooltip>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            aria-label="Search (⌘K)"
            aria-keyshortcuts="Meta+K Control+K"
            onClick={openCommandPalette}
            className={ICON_BTN}
          >
            <Search className="size-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="right" className="font-medium">
          Search ⌘K
        </TooltipContent>
      </Tooltip>
    </SidebarHeader>
  )
}

function CollapsedSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const currentTenantId = useTenantStore((s) => s.currentTenantId)

  const mainItems = MAIN_ITEMS.filter((i) => isItemEnabled(i, currentTenantId))
  const settingsItems = SETTINGS_ITEMS.filter((i) => isItemEnabled(i, currentTenantId))
  const allTos = [...TOP_ITEMS, ...mainItems, ...settingsItems].map((i) => i.to)
  const active = (to: string) => resolveActive(pathname, to, allTos)

  return (
    <TooltipProvider delayDuration={150} skipDelayDuration={300}>
      <CollapsedHeader />
      <SidebarContent className="items-stretch gap-0.5 px-1.5 py-1">
        <div className="flex flex-col">
          {TOP_ITEMS.map((item) => (
            <CollapsedNavLink key={item.label} {...item} isActive={active(item.to)} />
          ))}
        </div>
        <div className="mx-2 h-px bg-border" role="separator" />
        <div className="flex flex-col">
          {mainItems.map((item) => (
            <CollapsedNavLink key={item.label} {...item} isActive={active(item.to)} />
          ))}
        </div>
        {settingsItems.length > 0 && (
          <>
            <div className="mx-2 h-px bg-border" role="separator" />
            <div className="flex flex-col">
              {settingsItems.map((item) => (
                <CollapsedNavLink key={item.label} {...item} isActive={active(item.to)} />
              ))}
            </div>
          </>
        )}
      </SidebarContent>
    </TooltipProvider>
  )
}

// ─── Root export ──────────────────────────────────────────────────────────────

export function AppSidebar() {
  const { open } = useSidebar()
  return <Sidebar>{open ? <ExpandedSidebar /> : <CollapsedSidebar />}</Sidebar>
}
