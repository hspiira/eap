import { useQuery } from "@tanstack/react-query"
import { Link, useNavigate, useRouterState } from "@tanstack/react-router"
import {
  Bell,
  ChevronDown,
  HelpCircle,
  LogOut,
  Monitor,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Sun,
  User,
} from "lucide-react"

import { usersApi } from "@/api/endpoints/users"
import { openCommandPalette } from "@/components/CommandPalette"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { SidebarTrigger, useSidebar } from "@/components/ui/sidebar"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { useToast } from "@/contexts/ToastContext"
import { authActions } from "@/lib/auth-store"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/store/slices/authSlice"
import { useTenantStore } from "@/store/slices/tenantSlice"
import { useUIStore } from "@/store/slices/uiSlice"

const ROUTE_TITLES: Record<string, string> = {
  "/": "Home",
  "/at-risk": "At Risk",
  "/design": "Design gallery",
}

const ICON_BUTTON =
  "size-8 shrink-0 text-fg-muted hover:bg-surface-hover hover:text-fg"

function PageTitle() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const title = ROUTE_TITLES[pathname] ?? humaniseRoute(pathname)
  return (
    <span className="truncate text-sm font-medium text-fg">{title}</span>
  )
}

function humaniseRoute(pathname: string): string {
  if (pathname === "/") return "Home"
  const last = pathname.split("/").filter(Boolean).pop() ?? ""
  return last.charAt(0).toUpperCase() + last.slice(1).replace(/-/g, " ")
}

function HeaderSearch() {
  return (
    <button
      type="button"
      onClick={openCommandPalette}
      aria-label="Search (⌘K)"
      aria-keyshortcuts="Meta+K Control+K"
      className="relative hidden h-8 w-full max-w-80 cursor-pointer items-center gap-2 rounded-sm border border-border-subtle bg-surface px-3 text-sm text-fg-subtle transition-colors hover:border-border hover:bg-surface-hover md:flex"
    >
      <Search className="size-3.5 shrink-0" aria-hidden />
      <span className="flex-1 text-left">Search</span>
      <kbd
        aria-hidden
        className="inline-flex h-5 select-none items-center rounded-sm border border-border-subtle bg-bg px-1.5 font-mono text-[10px] font-medium"
      >
        ⌘K
      </kbd>
    </button>
  )
}

function HeaderSidebarTrigger() {
  const { open } = useSidebar()
  const Icon = open ? PanelLeftClose : PanelLeftOpen
  return (
    <SidebarTrigger className={ICON_BUTTON}>
      <Icon className="size-4" />
    </SidebarTrigger>
  )
}

function NotificationsDropdown() {
  const hasUnread = false
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={cn(ICON_BUTTON, "relative")}
          aria-label="Notifications"
        >
          <Bell className="size-4" />
          {hasUnread ? (
            <span
              className="absolute right-1.5 top-1.5 size-1.5 rounded-full bg-danger"
              aria-hidden
            />
          ) : null}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-72">
        <DropdownMenuLabel className="text-fg">Notifications</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <div className="px-2 py-3 text-center text-xs text-fg-muted">
          You're all caught up.
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function ThemeToggle() {
  const preference = useUIStore((s) => s.theme); const setPreference = useUIStore((s) => s.setTheme)
  const cycle = () => {
    const next: Array<"light" | "dark" | "system"> = ["light", "dark", "system"]
    const i = next.indexOf(preference)
    setPreference(next[(i + 1) % next.length])
  }
  const label =
    preference === "light"
      ? "Light"
      : preference === "dark"
        ? "Dark"
        : "System"
  const Icon = preference === "light" ? Sun : preference === "dark" ? Moon : Monitor
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={ICON_BUTTON}
          onClick={cycle}
          aria-label={`Theme: ${label}. Click to cycle.`}
        >
          <Icon className="size-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent side="bottom">Theme: {label}</TooltipContent>
    </Tooltip>
  )
}

function UserMenu() {
  const email = useAuthStore((s) => s.email)
  const userId = useAuthStore((s) => s.user_id)
  const tenantName = useTenantStore((s) => s.currentTenant?.name)
  const navigate = useNavigate()
  const { showSuccess } = useToast()

  const { data: user } = useQuery({
    queryKey: ["user", userId],
    queryFn: () => usersApi.getById(userId!),
    enabled: !!userId,
    staleTime: 5 * 60_000,
  })

  const displayEmail = email ?? "Account"
  const initial = displayEmail.charAt(0).toUpperCase()
  const role = user?.role ?? null

  const handleSignOut = async () => {
    await authActions.logout()
    showSuccess("Successfully signed out")
    navigate({
      to: "/auth/login",
      search: { tenant_code: undefined, email: undefined, redirect: undefined },
    })
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 gap-2 px-1.5 text-fg-muted hover:bg-surface-hover hover:text-fg"
          aria-label="Account menu"
        >
          <span
            className="grid size-6 shrink-0 place-items-center rounded-sm bg-primary/10 font-mono text-[10px] font-semibold text-primary"
            aria-hidden
          >
            {initial}
          </span>
          <span className="hidden max-w-32 truncate text-sm md:inline">
            {displayEmail}
          </span>
          <ChevronDown className="size-3.5 shrink-0" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="font-normal">
          <div className="flex items-center gap-2.5">
            <span
              className="grid size-8 shrink-0 place-items-center rounded-sm bg-primary/10 font-mono text-sm font-semibold text-primary"
              aria-hidden
            >
              {initial}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-fg">{displayEmail}</p>
              <p className="truncate text-xs text-fg-muted">
                {role ?? ""}
                {role && tenantName ? " · " : ""}
                {tenantName ?? ""}
              </p>
            </div>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link to="/me" className="cursor-pointer">
            <User className="size-4" />
            Profile
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="cursor-pointer"
          onSelect={(e) => {
            e.preventDefault()
            void handleSignOut()
          }}
        >
          <LogOut className="size-4" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function HelpButton() {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          asChild
          variant="ghost"
          size="icon"
          className={ICON_BUTTON}
          aria-label="Help & feedback"
        >
          <a href="#help">
            <HelpCircle className="size-4" />
          </a>
        </Button>
      </TooltipTrigger>
      <TooltipContent side="bottom">Help & feedback</TooltipContent>
    </Tooltip>
  )
}

export function DashboardHeader() {
  return (
    <TooltipProvider delayDuration={300}>
      <header
        className={cn(
          "sticky top-0 z-10 flex h-12 shrink-0 items-center gap-3 border-b border-border-subtle bg-bg pl-2 pr-3",
        )}
      >
        <HeaderSidebarTrigger />
        <div className="min-w-0 flex-1" aria-label="Breadcrumbs">
          <PageTitle />
        </div>
        <HeaderSearch />
        <div className="flex shrink-0 items-center gap-1">
          <NotificationsDropdown />
          <ThemeToggle />
          <UserMenu />
          <HelpButton />
        </div>
      </header>
    </TooltipProvider>
  )
}
