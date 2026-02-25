import { Link, useRouterState } from "@tanstack/react-router"
import {
  Home,
  Inbox,
  AlertCircle,
  Folder,
  FileText,
  Clock,
  Plus,
  ChevronDown,
  ChevronRight,
  Search,
  PanelLeft,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarTrigger,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubItem,
  SidebarMenuSubButton,
  sidebarStyles,
} from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"
import { useTenant } from "@/hooks/useTenant"

function toProperCase(s: string): string {
  return s
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ")
}

const PROJECT_LOGO = "/evexi%CC%81a.svg"

function TenantDisplay() {
  const { currentTenant } = useTenant()
  const displayName = currentTenant?.name ? toProperCase(currentTenant.name) : ""

  return (
    <div className={cn("flex w-full items-center gap-1.5 px-2", sidebarStyles.text, "font-semibold")}>
      <img src={PROJECT_LOGO} alt="" className="h-6 w-6 shrink-0 object-contain" />
      <span className="truncate">{displayName || "—"}</span>
    </div>
  )
}

const navItems: Array<{
  to: string
  label: string
  icon: typeof Home
  iconClassName?: string
}> = [
  { to: "/", label: "Home", icon: Home },
  { to: "#inbox", label: "Inbox", icon: Inbox },
  { to: "/at-risk", label: "At Risk", icon: AlertCircle, iconClassName: "text-[#D0B5B3]" },
]

function NavMain() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })

  return (
    <SidebarMenu>
      {navItems.map(({ to, label, icon: Icon, iconClassName }) => (
        <SidebarMenuItem key={label}>
          <SidebarMenuButton asChild isActive={to.startsWith("/") ? pathname === to : false}>
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

function PortfolioSection() {
  return (
    <SidebarGroup>
      <SidebarGroupLabel
        action={
          <button className={sidebarStyles.groupAction} aria-label="Add portfolio">
            <Plus className={sidebarStyles.icon} />
          </button>
        }
      >
        PORTFOLIO
      </SidebarGroupLabel>
      <SidebarMenu>
        <SidebarMenuItem className="border-b border-[#5A626A]/15">
          <Collapsible defaultOpen className="group/collapsible">
            <CollapsibleTrigger asChild>
              <button
                className={cn(
                  sidebarStyles.itemBase,
                  sidebarStyles.text,
                  sidebarStyles.hoverBg,
                  "outline-none [&[data-state=open]>svg]:rotate-0"
                )}
              >
                <Folder className={sidebarStyles.icon} />
                <span className="flex-1 text-left">Gulf Oil Ltd.</span>
                <ChevronDown className={cn(sidebarStyles.icon, "transition-transform group-data-[state=open]/collapsible:rotate-180")} />
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <SidebarMenuSub>
                <SidebarMenuSubItem>
                  <SidebarMenuSubButton asChild>
                    <a href="#global-brands">
                      <FileText className={sidebarStyles.icon} />
                      Global Brands
                    </a>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
                <SidebarMenuSubItem>
                  <SidebarMenuSubButton asChild>
                    <a href="#secondary-brands">
                      <FileText className={sidebarStyles.icon} />
                      Secondary Brands
                    </a>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
              </SidebarMenuSub>
            </CollapsibleContent>
          </Collapsible>
        </SidebarMenuItem>
        <SidebarMenuItem className="border-b border-[#5A626A]/15">
          <Collapsible className="group/collapsible">
            <CollapsibleTrigger asChild>
              <button
                className={cn(
                  sidebarStyles.itemBase,
                  sidebarStyles.text,
                  sidebarStyles.hoverBg,
                  "outline-none"
                )}
              >
                <Folder className={sidebarStyles.icon} />
                <span className="flex-1 text-left">Gulf Oil Asia</span>
                <ChevronRight className={cn(sidebarStyles.icon, "transition-transform group-data-[state=open]/collapsible:rotate-90")} />
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <SidebarMenuSub>
                <SidebarMenuSubItem>
                  <SidebarMenuSubButton asChild>
                    <a href="#">Sub-item</a>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
              </SidebarMenuSub>
            </CollapsibleContent>
          </Collapsible>
        </SidebarMenuItem>
        <SidebarMenuItem>
          <SidebarMenuButton asChild>
            <a href="#portfolio-all" className={sidebarStyles.textMutedHover}>
              … See all
            </a>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarGroup>
  )
}

const analyticsItems = [
  { to: "#overview", label: "Overview & Forecast", icon: Clock },
  { to: "#renewals", label: "Renewals", icon: Clock },
]

function AnalyticsSection() {
  return (
    <SidebarGroup>
      <SidebarGroupLabel>ANALYTICS</SidebarGroupLabel>
      <SidebarMenu>
        {analyticsItems.map(({ to, label, icon: Icon }) => (
          <SidebarMenuItem key={label}>
            <SidebarMenuButton asChild>
              <a href={to}>
                <Icon className={sidebarStyles.icon} />
                {label}
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  )
}

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarHeader>
        <div className={cn(sidebarStyles.borderedRow, "justify-between")}>
          <SidebarTrigger>
            <PanelLeft className={sidebarStyles.iconLg} />
          </SidebarTrigger>
        </div>
        <div className={cn(sidebarStyles.borderedRow, sidebarStyles.borderedRowBottom)}>
          <TenantDisplay />
        </div>
        <div className="space-y-2 px-2">
          <Button variant="secondary" className="mt-2 w-full justify-center" size="sm">
            NEW AGENT CHAT
          </Button>
          <div className={cn("relative", sidebarStyles.searchContainer)}>
            <Search className={cn("absolute left-2.5 top-1/2 -translate-y-1/2", sidebarStyles.icon, sidebarStyles.textMuted)} />
            <Input placeholder="Search" className="h-8 border-0 pl-8 pr-10 bg-transparent focus-visible:ring-0" />
            <kbd className={cn("pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-xs", sidebarStyles.searchShortcut, sidebarStyles.textMuted)}>
              ⌘K
            </kbd>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <NavMain />
        </SidebarGroup>
        <PortfolioSection />
        <AnalyticsSection />
      </SidebarContent>
    </Sidebar>
  )
}
