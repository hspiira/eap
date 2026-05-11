import { useEffect, useState } from "react"

import { Link, useRouterState } from "@tanstack/react-router"
import {
  Activity,
  AlertCircle,
  BarChart3,
  Briefcase,
  Building2,
  Calendar,
  ChevronRight,
  ClipboardCheck,
  FileCheck,
  FileSignature,
  FolderOpen,
  Handshake,
  Headphones,
  Home,
  Inbox,
  MessageSquare,
  PhoneCall,
  Search,
  ShieldCheck,
  Tag,
  UserCog,
  Users,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Input } from "@/components/ui/input"
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
import { type FeatureFlag,featureFlags } from "@/lib/featureFlags"
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
  return (import.meta.env.VITE_PLATFORM_TENANT_ID ?? '').trim()
}

type NavSection = {
  label: string
  items: ReadonlyArray<NavItem>
}

const TOP_ITEMS: ReadonlyArray<NavItem> = [
  { to: "/", label: "Home", icon: Home },
  { to: "/inbox", label: "Inbox", icon: Inbox },
  { to: "/at-risk", label: "At Risk", icon: AlertCircle, iconClassName: "text-danger" },
]

const SECTIONS: ReadonlyArray<NavSection> = [
  {
    label: "Organization & Clients",
    items: [
      { to: "/clients", label: "Clients", icon: Building2 },
      { to: "/industries", label: "Industries", icon: BarChart3 },
      { to: "/tags", label: "Tags", icon: Tag },
    ],
  },
  {
    label: "People",
    items: [
      { to: "/contacts", label: "Contacts", icon: Users, flag: "contacts" },
      { to: "/persons", label: "Persons", icon: Users },
      { to: "/users", label: "Platform Users", icon: UserCog },
    ],
  },
  {
    label: "Contracts & Billing",
    items: [
      { to: "/contracts", label: "Contracts", icon: FileSignature },
      { to: "/service-assignments", label: "Service Assignments", icon: FileCheck },
    ],
  },
  {
    label: "Services & Delivery",
    items: [
      { to: "/services", label: "Services", icon: Briefcase },
      { to: "/service-sessions", label: "Sessions", icon: Calendar },
    ],
  },
  {
    label: "Care Callbacks",
    items: [
      { to: "/care-callbacks", label: "Campaigns", icon: PhoneCall },
      { to: "/care-callbacks/worklist", label: "My worklist", icon: Headphones },
    ],
  },
  {
    label: "Surveys",
    items: [{ to: "/surveys", label: "Surveys", icon: MessageSquare }],
  },
  {
    label: "Consultancy",
    items: [{ to: "/engagements", label: "Engagements", icon: Handshake }],
  },
  {
    label: "Analytics & Performance",
    items: [{ to: "/kpis", label: "KPIs", icon: BarChart3, flag: "kpis" }],
  },
  {
    label: "Documents",
    items: [{ to: "/documents", label: "Documents", icon: FolderOpen, flag: "documents" }],
  },
  {
    label: "Audit & Compliance",
    items: [
      { to: "/audit", label: "Audits", icon: ClipboardCheck, flag: "audit" },
      { to: "/activities", label: "Activity Logs", icon: Activity, flag: "activities" },
    ],
  },
  {
    label: "Platform Admin",
    items: [
      { to: "/tenants", label: "Tenants", icon: ShieldCheck, platformAdmin: true },
    ],
  },
]

function isItemEnabled(item: NavItem, currentTenantId: string | null): boolean {
  if (item.flag && !featureFlags[item.flag]) return false
  if (item.platformAdmin) {
    const required = platformTenantId()
    if (required && currentTenantId !== required) return false
  }
  return true
}

function visibleSections(currentTenantId: string | null): NavSection[] {
  return SECTIONS.map((s) => ({
    ...s,
    items: s.items.filter((it) => isItemEnabled(it, currentTenantId)),
  })).filter((s) => s.items.length > 0)
}

function toProperCase(s: string): string {
  return s
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ")
}

function isRouteActive(pathname: string, to: string): boolean {
  if (to === "/") return pathname === "/"
  return pathname === to || pathname.startsWith(to + "/")
}

function findActiveSectionLabel(
  sections: ReadonlyArray<NavSection>,
  pathname: string,
): string | null {
  return (
    sections.find((s) => s.items.some((i) => isRouteActive(pathname, i.to)))?.label ?? null
  )
}

function useTenantDisplayName(): string {
  const currentTenant = useTenantStore((s) => s.currentTenant)
  return currentTenant?.name ? toProperCase(currentTenant.name) : "—"
}

function ExpandedHeader() {
  const displayName = useTenantDisplayName()
  return (
    <SidebarHeader>
      <div className="flex h-8 items-center gap-2 px-2 text-sm font-semibold text-sidebar-foreground">
        <img src={PROJECT_LOGO} alt="" className="h-5 w-5 shrink-0 object-contain" />
        <span className="truncate">{displayName}</span>
      </div>
      <div className="relative">
        <Search className="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-sidebar-foreground/60" />
        <Input
          placeholder="Search"
          aria-label="Search"
          className="h-8 border-sidebar-border bg-sidebar pl-7 text-sm focus-visible:ring-sidebar-ring"
        />
      </div>
    </SidebarHeader>
  )
}

function ExpandedTopItems() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  return (
    <SidebarMenu>
      {TOP_ITEMS.map(({ to, label, icon: Icon, iconClassName }) => (
        <SidebarMenuItem key={label}>
          <SidebarMenuButton asChild isActive={isRouteActive(pathname, to)}>
            <Link to={to}>
              <Icon className={iconClassName} />
              <span>{label}</span>
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
      ))}
    </SidebarMenu>
  )
}

interface ExpandedSectionProps extends NavSection {
  open: boolean
  onOpenChange: (open: boolean) => void
}

function ExpandedSection({ label, items, open, onOpenChange }: ExpandedSectionProps) {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  return (
    <SidebarGroup>
      <Collapsible open={open} onOpenChange={onOpenChange} className="group/collapsible">
        <CollapsibleTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            className="h-auto w-full justify-start gap-2 rounded-sm px-2 py-1.5 text-xs font-semibold tracking-wide text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-sidebar-ring focus-visible:ring-offset-sidebar [&[data-state=open]>svg]:rotate-90"
          >
            <ChevronRight className="size-3.5 shrink-0 transition-transform" />
            {label}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <SidebarMenu>
            {items.map(({ to, label: itemLabel, icon: Icon, iconClassName }) => (
              <SidebarMenuItem key={itemLabel}>
                <SidebarMenuButton asChild isActive={isRouteActive(pathname, to)}>
                  <Link to={to}>
                    <Icon className={iconClassName} />
                    <span>{itemLabel}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </CollapsibleContent>
      </Collapsible>
    </SidebarGroup>
  )
}

function ExpandedSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const currentTenantId = useTenantStore((s) => s.currentTenantId)
  const sections = visibleSections(currentTenantId)
  const [openSection, setOpenSection] = useState<string | null>(
    () => findActiveSectionLabel(sections, pathname) ?? sections[0]?.label ?? null,
  )

  useEffect(() => {
    const active = findActiveSectionLabel(sections, pathname)
    if (active) setOpenSection(active)
  }, [pathname, sections])

  return (
    <>
      <ExpandedHeader />
      <SidebarContent>
        <SidebarGroup>
          <ExpandedTopItems />
        </SidebarGroup>
        {sections.map((section) => (
          <ExpandedSection
            key={section.label}
            {...section}
            open={openSection === section.label}
            onOpenChange={(next) => setOpenSection(next ? section.label : null)}
          />
        ))}
      </SidebarContent>
    </>
  )
}

const COLLAPSED_ICON_BTN =
  "relative grid h-9 w-9 mx-auto place-items-center rounded-md text-sidebar-foreground/75 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring"

interface CollapsedNavLinkProps {
  to: string
  label: string
  icon: React.ElementType
  iconClassName?: string
  isActive: boolean
}

function CollapsedNavLink({
  to,
  label,
  icon: Icon,
  iconClassName,
  isActive,
}: CollapsedNavLinkProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Link
          to={to}
          aria-label={label}
          aria-current={isActive ? "page" : undefined}
          className={cn(
            COLLAPSED_ICON_BTN,
            isActive && "bg-sidebar-accent text-sidebar-accent-foreground",
          )}
        >
          {isActive ? (
            <span
              aria-hidden
              className="absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-r bg-sidebar-primary"
            />
          ) : null}
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
    <SidebarHeader className="items-center gap-1 border-b border-sidebar-border pb-2">
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
            aria-label="Search"
            onClick={() => setOpen(true)}
            className={COLLAPSED_ICON_BTN}
          >
            <Search className="size-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="right" className="font-medium">
          Search
          <kbd className="ml-2 rounded-sm border border-primary-foreground/20 px-1 font-mono text-[10px]">
            ⌘K
          </kbd>
        </TooltipContent>
      </Tooltip>
    </SidebarHeader>
  )
}

function CollapsedSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const currentTenantId = useTenantStore((s) => s.currentTenantId)
  const sections = visibleSections(currentTenantId)
  return (
    <TooltipProvider delayDuration={150} skipDelayDuration={300}>
      <CollapsedHeader />
      <SidebarContent className="items-stretch gap-1.5 px-1.5 py-2">
        <div className="flex flex-col gap-0.5">
          {TOP_ITEMS.map((item) => (
            <CollapsedNavLink
              key={item.label}
              to={item.to}
              label={item.label}
              icon={item.icon}
              iconClassName={item.iconClassName}
              isActive={isRouteActive(pathname, item.to)}
            />
          ))}
        </div>
        <div className="mx-2 h-px bg-sidebar-border" role="separator" />
        <div className="flex flex-col gap-0.5">
          {sections.map((section) => {
            const primary = section.items[0]
            const sectionActive = section.items.some((i) => isRouteActive(pathname, i.to))
            return (
              <CollapsedNavLink
                key={section.label}
                to={primary.to}
                label={section.label}
                icon={primary.icon}
                isActive={sectionActive}
              />
            )
          })}
        </div>
      </SidebarContent>
    </TooltipProvider>
  )
}

export function AppSidebar() {
  const { open } = useSidebar()
  return <Sidebar>{open ? <ExpandedSidebar /> : <CollapsedSidebar />}</Sidebar>
}
