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

function TenantDisplay() {
  return (
    <div className={cn("flex w-full items-center gap-1.5 px-2", sidebarStyles.text, "font-semibold")}>
      <span className={sidebarStyles.contextIconBox}>G</span>
      <span className="truncate">GULF GLOBAL</span>
    </div>
  )
}

function NavMain() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const navItems = [
    { to: "/", label: "Home", icon: Home },
    { to: "#inbox", label: "Inbox", icon: Inbox },
    { to: "#at-risk", label: "At Risk", icon: AlertCircle, iconClassName: "text-[#D0B5B3]" },
  ] as const

  return (
    <SidebarMenu>
      {navItems.map(({ to, label, icon: Icon, iconClassName }) => (
        <SidebarMenuItem key={label}>
          <SidebarMenuButton asChild isActive={to === "/" ? pathname === "/" : false}>
            <Link to={to}>
              <Icon className={cn(sidebarStyles.icon, iconClassName)} />
              <span>{label}</span>
            </Link>
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
        <SidebarMenuItem>
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
                    <Link to="#global-brands">
                      <FileText className={sidebarStyles.icon} />
                      Global Brands
                    </Link>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
                <SidebarMenuSubItem>
                  <SidebarMenuSubButton asChild>
                    <Link to="#secondary-brands">
                      <FileText className={sidebarStyles.icon} />
                      Secondary Brands
                    </Link>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
              </SidebarMenuSub>
            </CollapsibleContent>
          </Collapsible>
        </SidebarMenuItem>
        <SidebarMenuItem>
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
                    <Link to="#">Sub-item</Link>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
              </SidebarMenuSub>
            </CollapsibleContent>
          </Collapsible>
        </SidebarMenuItem>
        <SidebarMenuItem>
          <SidebarMenuButton asChild>
            <Link to="#portfolio-all" className={sidebarStyles.textMutedHover}>
              … See all
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarGroup>
  )
}

function AnalyticsSection() {
  const items = [
    { to: "#overview", label: "Overview & Forecast", icon: Clock },
    { to: "#renewals", label: "Renewals", icon: Clock },
  ] as const

  return (
    <SidebarGroup>
      <SidebarGroupLabel>ANALYTICS</SidebarGroupLabel>
      <SidebarMenu>
        {items.map(({ to, label, icon: Icon }) => (
          <SidebarMenuItem key={label}>
            <SidebarMenuButton asChild>
              <Link to={to}>
                <Icon className={sidebarStyles.icon} />
                {label}
              </Link>
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
