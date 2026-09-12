import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import {
  Check,
  ChevronDown,
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
import { accountDisplayName, toProperCase } from "@/lib/display"
import { queryKeys } from "@/lib/query-keys"
import { openGlobalSearch } from "@/lib/search-state"
import { signOutAndRedirect } from "@/lib/sign-out"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/store/slices/authSlice"
import { useTenantStore } from "@/store/slices/tenantSlice"
import { useUIStore } from "@/store/slices/uiSlice"

const ICON_BUTTON = "size-8 shrink-0 text-fg-muted hover:bg-surface-hover hover:text-fg"

const THEMES = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
] as const

/** The workspace the session is in. A client organisation is not a workspace. */
function useWorkspaceName(): string | null {
  const name = useTenantStore((s) => s.currentTenant?.name)
  return name ? toProperCase(name) : null
}

function WorkspaceName() {
  const name = useWorkspaceName()
  if (!name) return null
  return (
    <span className="min-w-0 truncate text-sm font-medium text-fg" title={name}>
      {name}
    </span>
  )
}

function HeaderSidebarTrigger() {
  const { open } = useSidebar()
  const Icon = open ? PanelLeftClose : PanelLeftOpen
  return (
    <SidebarTrigger
      className={ICON_BUTTON}
      aria-label={open ? "Collapse sidebar" : "Expand sidebar"}
    >
      <Icon className="size-4" />
    </SidebarTrigger>
  )
}

/**
 * The one global search control. A field-like button on desktop and an icon on
 * mobile, both opening the same dialog, which also answers Cmd/Ctrl+K.
 */
function SearchLauncher() {
  return (
    <>
      <Button
        type="button"
        variant="outline"
        onClick={openGlobalSearch}
        aria-label="Search (⌘K)"
        aria-keyshortcuts="Meta+K Control+K"
        className="relative hidden h-8 w-full max-w-96 cursor-pointer items-center justify-start gap-2 rounded-sm border-border-subtle bg-surface px-3 text-sm font-normal text-fg-subtle transition-colors hover:border-border hover:bg-surface-hover md:flex"
      >
        <Search className="size-3.5 shrink-0" aria-hidden />
        <span className="flex-1 truncate text-left">Search clients, practitioners…</span>
        <kbd
          aria-hidden
          className="inline-flex h-5 select-none items-center rounded-sm border border-border-subtle bg-bg px-1.5 text-[10px] font-medium"
        >
          ⌘K
        </kbd>
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={openGlobalSearch}
        aria-label="Search"
        className={cn(ICON_BUTTON, "md:hidden")}
      >
        <Search className="size-4" />
      </Button>
    </>
  )
}

function AppearanceSection() {
  const preference = useUIStore((s) => s.theme)
  const setPreference = useUIStore((s) => s.setTheme)
  return (
    <>
      <DropdownMenuLabel className="text-xs font-normal text-fg-muted">
        Appearance
      </DropdownMenuLabel>
      {THEMES.map((theme) => (
        <DropdownMenuItem
          key={theme.value}
          className="cursor-pointer"
          onSelect={(e) => {
            e.preventDefault()
            setPreference(theme.value)
          }}
        >
          <theme.icon className="size-4" />
          {theme.label}
          {preference === theme.value ? <Check className="ml-auto size-3.5" /> : null}
        </DropdownMenuItem>
      ))}
    </>
  )
}

/** The account's name. The email is detail inside the menu, not the label. */
function useAccountIdentity() {
  const email = useAuthStore((s) => s.email)
  const userId = useAuthStore((s) => s.user_id)

  const { data: user } = useQuery({
    queryKey: queryKeys.users.detail(userId ?? ""),
    queryFn: () => usersApi.getById(userId!),
    enabled: !!userId,
    staleTime: 5 * 60_000,
  })

  const name = accountDisplayName(user?.display_name, email)
  return {
    name,
    email: email ?? null,
    primary: name ?? "Account",
    role: user?.role ?? null,
  }
}

function AccountAvatar({ label, size }: { label: string; size: "sm" | "md" }) {
  return (
    <span
      className={cn(
        "grid shrink-0 place-items-center rounded-sm bg-fg/6 font-semibold text-fg-muted",
        size === "sm" ? "size-6 text-[10px]" : "size-8 text-sm",
      )}
      aria-hidden
    >
      {label.charAt(0).toUpperCase()}
    </span>
  )
}

function UserMenu() {
  const identity = useAccountIdentity()
  const tenantName = useWorkspaceName()

  const handleSignOut = () => {
    void signOutAndRedirect()
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
          <AccountAvatar label={identity.primary} size="sm" />
          <span className="hidden max-w-32 truncate text-sm md:inline">{identity.primary}</span>
          <ChevronDown className="size-3.5 shrink-0" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="font-normal">
          <div className="flex items-center gap-2.5">
            <AccountAvatar label={identity.primary} size="md" />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-fg">{identity.primary}</p>
              {identity.email ? (
                <p className="truncate text-xs text-fg-muted">{identity.email}</p>
              ) : null}
              <p className="truncate text-xs text-fg-muted">
                {identity.role ?? ""}
                {identity.role && tenantName ? " · " : ""}
                {tenantName ?? ""}
              </p>
            </div>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link to="/me" className="cursor-pointer">
            <User className="size-4" />
            My profile
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <AppearanceSection />
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

/**
 * Sidebar control and workspace, one search control, one account menu.
 *
 * No page title here: every page renders its own breadcrumb and heading, and
 * two titles for one page is one too many. No notification bell and no help
 * link either, until there is an event source and a support destination for
 * them to point at.
 */
export function DashboardHeader() {
  return (
    <header className="sticky top-0 z-10 flex h-12 shrink-0 items-center gap-3 border-b border-border-subtle bg-bg pl-2 pr-3">
      <HeaderSidebarTrigger />
      <WorkspaceName />
      <div className="flex min-w-0 flex-1 justify-end md:justify-center">
        <SearchLauncher />
      </div>
      <UserMenu />
    </header>
  )
}
