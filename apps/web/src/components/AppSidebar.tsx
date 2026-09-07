import { Link, useRouterState } from "@tanstack/react-router"

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
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { useEnabledNavItems } from "@/hooks/useNavigation"
import { isComingSoon, type NavItem, resolveActive } from "@/lib/navigation"
import { cn } from "@/lib/utils"

const PROJECT_LOGO = "/evexia.png"
const PRODUCT_NAME = "Evexía"

/**
 * The sidebar is module navigation only.
 *
 * The workspace name and the search launcher live in the app header, which is
 * visible in both sidebar states; duplicating either here gave the same
 * control two places to be. Expanding and collapsing is the header's trigger,
 * so there is one such control rather than two.
 */

// ─── Expanded sidebar ────────────────────────────────────────────────────────

function ExpandedHeader() {
  return (
    <SidebarHeader className="gap-0 pb-1">
      <div className="flex h-11 items-center gap-2.5 px-2">
        <img src={PROJECT_LOGO} alt="" className="h-5 w-5 shrink-0 object-contain" />
        <span className="truncate text-sm font-semibold text-fg">{PRODUCT_NAME}</span>
      </div>
    </SidebarHeader>
  )
}

function ComingSoonNavItem({ label, icon: Icon, iconClassName }: NavItem) {
  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        disabled
        title={`${label} is not available yet`}
        className="cursor-not-allowed opacity-50 hover:bg-transparent"
      >
        <Icon className={iconClassName} />
        <span>{label}</span>
        <span className="ml-auto text-[10px] font-medium tracking-wide text-fg-subtle/70">
          Soon
        </span>
      </SidebarMenuButton>
    </SidebarMenuItem>
  )
}

function ExpandedNavItem(props: NavItem & { isActive: boolean }) {
  const { to, label, icon: Icon, iconClassName, isActive } = props
  if (isComingSoon(props)) return <ComingSoonNavItem {...props} />
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

function ExpandedGroup({
  items,
  label,
  isActive,
}: {
  items: NavItem[]
  label?: string
  isActive: (item: NavItem) => boolean
}) {
  if (items.length === 0) return null
  return (
    <>
      <div className="mx-2 my-1 h-px bg-border" role="separator" />
      <SidebarGroup className="gap-0">
        {label ? (
          <p className="px-2 pb-0.5 pt-1 text-[10px] font-medium tracking-widest text-fg-subtle/60">
            {label}
          </p>
        ) : null}
        <SidebarMenu>
          {items.map((item) => (
            <ExpandedNavItem key={item.label} {...item} isActive={isActive(item)} />
          ))}
        </SidebarMenu>
      </SidebarGroup>
    </>
  )
}

function ExpandedSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const nav = useEnabledNavItems()
  const isActive = (item: NavItem) => resolveActive(pathname, item, nav.prefixes)

  return (
    <>
      <ExpandedHeader />
      <SidebarContent className="gap-0 px-2 py-1">
        <SidebarGroup className="gap-0">
          <SidebarMenu>
            {nav.top.map((item) => (
              <ExpandedNavItem key={item.label} {...item} isActive={isActive(item)} />
            ))}
          </SidebarMenu>
        </SidebarGroup>
        <ExpandedGroup items={nav.main} isActive={isActive} />
        <ExpandedGroup items={nav.settings} label="SETTINGS" isActive={isActive} />
      </SidebarContent>
    </>
  )
}

// ─── Collapsed sidebar ────────────────────────────────────────────────────────

const ICON_BTN =
  "relative grid h-7 w-7 mx-auto place-items-center rounded-sm text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring"

function ComingSoonCollapsedNavLink({ label, icon: Icon, iconClassName }: NavItem) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          aria-disabled="true"
          aria-label={`${label}: not available yet`}
          className={cn(ICON_BTN, "cursor-not-allowed opacity-40 hover:bg-transparent")}
        >
          <Icon className={cn("size-4", iconClassName)} />
        </span>
      </TooltipTrigger>
      <TooltipContent side="right" className="font-medium">
        {label} (soon)
      </TooltipContent>
    </Tooltip>
  )
}

function CollapsedNavLink(props: NavItem & { isActive: boolean }) {
  const { to, label, icon: Icon, iconClassName, isActive } = props
  if (isComingSoon(props)) return <ComingSoonCollapsedNavLink {...props} />
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
  return (
    <SidebarHeader className="items-center gap-1 pb-2">
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="mx-auto grid size-9 place-items-center">
            <img src={PROJECT_LOGO} alt={PRODUCT_NAME} className="h-5 w-5 object-contain" />
          </span>
        </TooltipTrigger>
        <TooltipContent side="right" className="font-medium">
          {PRODUCT_NAME}
        </TooltipContent>
      </Tooltip>
    </SidebarHeader>
  )
}

function CollapsedGroup({
  items,
  isActive,
}: {
  items: NavItem[]
  isActive: (item: NavItem) => boolean
}) {
  if (items.length === 0) return null
  return (
    <>
      <div className="mx-2 h-px bg-border" role="separator" />
      <div className="flex flex-col">
        {items.map((item) => (
          <CollapsedNavLink key={item.label} {...item} isActive={isActive(item)} />
        ))}
      </div>
    </>
  )
}

function CollapsedSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const nav = useEnabledNavItems()
  const isActive = (item: NavItem) => resolveActive(pathname, item, nav.prefixes)

  return (
    <TooltipProvider delayDuration={150} skipDelayDuration={300}>
      <CollapsedHeader />
      <SidebarContent className="items-stretch gap-0.5 px-1.5 py-1">
        <div className="flex flex-col">
          {nav.top.map((item) => (
            <CollapsedNavLink key={item.label} {...item} isActive={isActive(item)} />
          ))}
        </div>
        <CollapsedGroup items={nav.main} isActive={isActive} />
        <CollapsedGroup items={nav.settings} isActive={isActive} />
      </SidebarContent>
    </TooltipProvider>
  )
}

// ─── Root export ──────────────────────────────────────────────────────────────

export function AppSidebar() {
  const { open } = useSidebar()
  return <Sidebar>{open ? <ExpandedSidebar /> : <CollapsedSidebar />}</Sidebar>
}
