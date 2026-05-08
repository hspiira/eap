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
  Headphones,
  Home,
  Inbox,
  LayoutList,
  PhoneCall,
  Tag,
  UserCircle,
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
  sidebarStyles,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"
import { useTenantStore } from "@/store/slices/tenantSlice"

function toProperCase(s: string): string {
  return s
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ")
}

const PROJECT_LOGO = "/evexi%CC%81a.svg"

function TenantDisplay() {
  const currentTenant = useTenantStore((s) => s.currentTenant)
  const displayName = currentTenant?.name ? toProperCase(currentTenant.name) : ""

  return (
    <div className={cn("flex w-full items-center gap-1.5 px-2", sidebarStyles.text, "font-semibold")}>
      <img src={PROJECT_LOGO} alt="" className="h-6 w-6 shrink-0 object-contain" />
      <span className="truncate">{displayName || "—"}</span>
    </div>
  )
}

function NavTop() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })

  const items = [
    { to: "/", label: "Home", icon: Home },
    { to: "/inbox", label: "Inbox", icon: Inbox },
    { to: "/at-risk", label: "At Risk", icon: AlertCircle, iconClassName: "text-danger-soft" },
  ] as const

  return (
    <SidebarMenu>
      {items.map(({ to, label, icon: Icon, iconClassName }) => (
        <SidebarMenuItem key={label}>
          <SidebarMenuButton asChild isActive={pathname === (to.startsWith("/") ? to : pathname)}>
            {to.startsWith("/") ? (
              <Link to={to}>
                <Icon className={cn(sidebarStyles.icon, iconClassName)} />
                <span>{label}</span>
              </Link>
            ) : (
              <a href={to}>
                <Icon className={cn(sidebarStyles.icon, iconClassName)} />
                <span>{label}</span>
              </a>
            )}
          </SidebarMenuButton>
        </SidebarMenuItem>
      ))}
    </SidebarMenu>
  )
}

function SidebarSection({
  label,
  defaultOpen = false,
  items,
}: {
  label: string
  defaultOpen?: boolean
  items: Array<{ to: string; label: string; icon: React.ElementType }>
}) {
  const pathname = useRouterState({ select: (s) => s.location.pathname }) as string

  return (
    <SidebarGroup>
      <Collapsible defaultOpen={defaultOpen} className="group/collapsible">
        <CollapsibleTrigger asChild>
          <button
            className={cn(
              "flex w-full items-center gap-1.5 px-2 py-1.5 text-xs font-semibold uppercase tracking-wider",
              sidebarStyles.text,
              sidebarStyles.hoverBg,
              "outline-none rounded-none [&[data-state=open]>svg]:rotate-90"
            )}
          >
            <ChevronRight className={cn(sidebarStyles.icon, "transition-transform")} />
            {label}
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <SidebarMenu>
            {items.map(({ to, label: itemLabel, icon: Icon }) => (
              <SidebarMenuItem key={itemLabel}>
                <SidebarMenuButton asChild isActive={pathname === to}>
                  <Link to={to}>
                    <Icon className={sidebarStyles.icon} />
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
        <div className={cn(sidebarStyles.borderedRow, "justify-between")}>
          <SidebarTrigger>
            <LayoutList className={sidebarStyles.iconLg} />
          </SidebarTrigger>
        </div>
        <div className={cn(sidebarStyles.borderedRow, sidebarStyles.borderedRowBottom)}>
          <TenantDisplay />
        </div>
        <div className="space-y-2 px-2">
          <div className={cn("relative", sidebarStyles.searchContainer)}>
            <Input placeholder="Search" className="h-8 border-0 pl-8 pr-10 bg-transparent focus-visible:ring-0 rounded-none" />
          </div>
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
            { to: "/persons", label: "Client Employees", icon: UserCircle },
            { to: "/persons", label: "Dependents", icon: Users },
            { to: "/persons", label: "Platform Staff", icon: UserCog },
            { to: "/persons", label: "Service Providers", icon: Briefcase },
            { to: "/users", label: "Users", icon: UserCog },
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
          label="Analytics & Performance"
          items={[
            { to: "/kpis", label: "KPIs", icon: BarChart3 },
          ]}
        />
        <SidebarSection
          label="Documents"
          items={[
            { to: "/documents", label: "Documents", icon: FolderOpen },
          ]}
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
