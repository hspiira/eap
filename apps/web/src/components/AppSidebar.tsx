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
  Tag,
  UserCog,
  Users,
} from "lucide-react"

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
} from "@/components/ui/sidebar"
import { useTenantStore } from "@/store/slices/tenantSlice"

const PROJECT_LOGO = "/evexi%CC%81a.svg"

function toProperCase(s: string): string {
  return s
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ")
}

function TenantDisplay() {
  const currentTenant = useTenantStore((s) => s.currentTenant)
  const displayName = currentTenant?.name ? toProperCase(currentTenant.name) : ""

  return (
    <div className="flex w-full items-center gap-2 px-2 text-sm font-semibold text-sidebar-foreground">
      <img src={PROJECT_LOGO} alt="" className="h-5 w-5 shrink-0 object-contain" />
      <span className="truncate">{displayName || "—"}</span>
    </div>
  )
}

type TopItem = {
  to: string
  label: string
  icon: React.ElementType
  iconClassName?: string
}

const TOP_ITEMS: ReadonlyArray<TopItem> = [
  { to: "/", label: "Home", icon: Home },
  { to: "/inbox", label: "Inbox", icon: Inbox },
  { to: "/at-risk", label: "At Risk", icon: AlertCircle, iconClassName: "text-danger" },
]

function NavTop() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })

  return (
    <SidebarMenu>
      {TOP_ITEMS.map(({ to, label, icon: Icon, iconClassName }) => (
        <SidebarMenuItem key={label}>
          <SidebarMenuButton asChild isActive={pathname === to}>
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

interface SidebarSectionProps {
  label: string
  defaultOpen?: boolean
  items: ReadonlyArray<{ to: string; label: string; icon: React.ElementType }>
}

function SidebarSection({ label, defaultOpen = false, items }: SidebarSectionProps) {
  const pathname = useRouterState({ select: (s) => s.location.pathname })

  return (
    <SidebarGroup>
      <Collapsible defaultOpen={defaultOpen} className="group/collapsible">
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-xs font-semibold uppercase tracking-wider text-sidebar-foreground/70 outline-none transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 focus-visible:ring-sidebar-ring focus-visible:ring-offset-2 focus-visible:ring-offset-sidebar [&[data-state=open]>svg]:rotate-90"
          >
            <ChevronRight className="size-3.5 shrink-0 transition-transform" />
            {label}
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <SidebarMenu>
            {items.map(({ to, label: itemLabel, icon: Icon }) => (
              <SidebarMenuItem key={itemLabel}>
                <SidebarMenuButton asChild isActive={pathname === to}>
                  <Link to={to}>
                    <Icon />
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

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex h-8 items-center">
          <TenantDisplay />
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
      <SidebarContent>
        <SidebarGroup>
          <NavTop />
        </SidebarGroup>
        <SidebarSection
          label="Organization & Clients"
          defaultOpen
          items={[
            { to: "/clients", label: "Clients", icon: Building2 },
            { to: "/industries", label: "Industries", icon: BarChart3 },
            { to: "/tags", label: "Tags", icon: Tag },
          ]}
        />
        <SidebarSection
          label="People"
          items={[
            { to: "/persons", label: "Persons", icon: Users },
            { to: "/users", label: "Platform Users", icon: UserCog },
          ]}
        />
        <SidebarSection
          label="Contracts & Billing"
          items={[
            { to: "/contracts", label: "Contracts", icon: FileSignature },
            { to: "/service-assignments", label: "Service Assignments", icon: FileCheck },
          ]}
        />
        <SidebarSection
          label="Services & Delivery"
          items={[
            { to: "/services", label: "Services", icon: Briefcase },
            { to: "/service-sessions", label: "Sessions", icon: Calendar },
          ]}
        />
        <SidebarSection
          label="Care Callbacks"
          items={[
            { to: "/care-callbacks", label: "Campaigns", icon: PhoneCall },
            { to: "/care-callbacks/worklist", label: "My worklist", icon: Headphones },
          ]}
        />
        <SidebarSection
          label="Surveys"
          items={[{ to: "/surveys", label: "Surveys", icon: MessageSquare }]}
        />
        <SidebarSection
          label="Consultancy"
          items={[{ to: "/engagements", label: "Engagements", icon: Handshake }]}
        />
        <SidebarSection
          label="Analytics & Performance"
          items={[{ to: "/kpis", label: "KPIs", icon: BarChart3 }]}
        />
        <SidebarSection
          label="Documents"
          items={[{ to: "/documents", label: "Documents", icon: FolderOpen }]}
        />
        <SidebarSection
          label="Audit & Compliance"
          items={[
            { to: "/audit", label: "Audits", icon: ClipboardCheck },
            { to: "/activities", label: "Activity Logs", icon: Activity },
          ]}
        />
      </SidebarContent>
    </Sidebar>
  )
}

