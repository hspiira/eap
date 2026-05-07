import { useEffect, useRef } from "react"

import { useRouterState } from "@tanstack/react-router"
import { Link } from "@tanstack/react-router"
import { useNavigate } from "@tanstack/react-router"
import {
  Bell,
  ChevronDown,
  HelpCircle,
  LogOut,
  Monitor,
  Moon,
  Search,
  Settings,
  Sun,
  User,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { sidebarStyles } from "@/components/ui/sidebar"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { useTheme } from "@/contexts/ThemeContext"
import { useToast } from "@/contexts/ToastContext"
import { authActions } from "@/lib/auth-store"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/store/slices/authSlice"

const routeTitles: Record<string, string> = {
  "/": "Home",
  "/at-risk": "At Risk",
}

function PageTitle() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const title = routeTitles[pathname] ?? "Dashboard"
  return (
    <span className="text-sm font-medium text-[#5A626A] truncate">
      {title}
    </span>
  )
}

function HeaderSearch() {
  const inputRef = useRef<HTMLInputElement>(null)
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [])
  return (
    <div className="relative h-8 min-w-[200px] max-w-[320px] rounded-none bg-[#f5f5f5] px-2">
      <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 shrink-0 text-black/80" />
      <Input
        ref={inputRef}
        placeholder="Search"
        className="h-full min-h-0 border-0 bg-transparent pl-8 pr-10 py-0 text-sm focus-visible:ring-0"
        onKeyDown={(e) => e.stopPropagation()}
      />
      <kbd className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 px-1.5 py-0.5 text-xs text-black/80 bg-[#5A626A]/15 rounded-none">
        ⌘K
      </kbd>
    </div>
  )
}

function NotificationsDropdown() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="relative h-8 w-8 p-0 text-[#5A626A] hover:bg-[#E6E0D7]"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          <span
            className="absolute right-1 top-1 h-1.5 w-1.5 bg-[#b85c4a]"
            aria-hidden
          />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-72">
        <DropdownMenuLabel className="text-[#5A626A]">
          Notifications
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="cursor-pointer text-sm text-[#5A626A]"
          onSelect={() => {
            setTimeout(() => {
              document.querySelector('[data-notifications-card]')?.scrollIntoView({ behavior: 'smooth' })
            }, 0)
          }}
        >
          <span className="truncate">Captiva 01 121 PHA – Speeding</span>
        </DropdownMenuItem>
        <DropdownMenuItem
          className="cursor-pointer text-sm text-[#5A626A]"
          onSelect={() => {
            setTimeout(() => {
              document.querySelector('[data-notifications-card]')?.scrollIntoView({ behavior: 'smooth' })
            }, 0)
          }}
        >
          <span className="truncate">Howo Авт 01 054 JKA – Exited geofence</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="cursor-pointer text-sm font-medium text-[#5A626A]"
          onSelect={() => {
            setTimeout(() => {
              document.querySelector('[data-notifications-card]')?.scrollIntoView({ behavior: 'smooth' })
            }, 0)
          }}
        >
          View all notifications
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function ThemeToggle() {
  const { preference, setPreference } = useTheme()
  const cycle = () => {
    const next: Array<"light" | "dark" | "system"> = ["light", "dark", "system"]
    const i = next.indexOf(preference)
    setPreference(next[(i + 1) % 3])
  }
  const label =
    preference === "light"
      ? "Light"
      : preference === "dark"
        ? "Dark"
        : "System"
  const Icon = preference === "light" ? Sun : preference === "dark" ? Moon : Monitor
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-[#5A626A] hover:bg-[#E6E0D7]"
            onClick={cycle}
            aria-label={`Theme: ${label}`}
          >
            <Icon className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent
          side="bottom"
          className="border border-[#5A626A]/20 bg-[#E6E0D7] text-[#5A626A] rounded-none"
        >
          Theme: {label}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

function UserMenu() {
  const email = useAuthStore((s) => s.email)
  const navigate = useNavigate()
  const { showSuccess } = useToast()
  const displayEmail = email ?? "Account"

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
          className="h-8 gap-2 px-2 text-[#5A626A] hover:bg-[#E6E0D7]"
          aria-label="Account menu"
        >
          <span className="flex h-6 w-6 shrink-0 items-center justify-center border border-[#5A626A]/30 bg-[#E6E0D7] text-xs font-medium text-[#5A626A]">
            {displayEmail.charAt(0).toUpperCase()}
          </span>
          <span className="max-w-[120px] truncate text-sm">{displayEmail}</span>
          <ChevronDown className="h-4 w-4 shrink-0 opacity-70" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="text-[#5A626A] font-normal">
          <span className="truncate">{displayEmail}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link
            to="/"
            className="cursor-pointer text-[#5A626A]"
          >
            <User className="mr-2 h-4 w-4" />
            Profile
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link
            to="/"
            className="cursor-pointer text-[#5A626A]"
          >
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="cursor-pointer text-[#5A626A] focus:bg-[#E0DAD2]"
          onSelect={(e) => {
            e.preventDefault()
            handleSignOut()
          }}
        >
          <LogOut className="mr-2 h-4 w-4" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function HelpLink() {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <a
            href="#"
            className="flex h-8 w-8 shrink-0 items-center justify-center text-[#5A626A] hover:bg-[#E6E0D7]"
            aria-label="Help & feedback"
          >
            <HelpCircle className="h-4 w-4" />
          </a>
        </TooltipTrigger>
        <TooltipContent
          side="bottom"
          className="border border-[#5A626A]/20 bg-[#E6E0D7] text-[#5A626A] rounded-none"
        >
          Help & feedback
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

export function DashboardHeader() {
  return (
    <header
      className={cn(
        "h-10 flex items-center rounded-none bg-[#fafafa]",
        sidebarStyles.borderedRowBottom,
        "sticky top-0 z-10 shrink-0"
      )}
    >
      <div className="flex w-full items-center gap-4 px-2">
        <div className="min-w-0 flex-1" aria-label="Breadcrumbs">
          <PageTitle />
        </div>
        <div className="flex shrink-0 items-center gap-2">
        <HeaderSearch />
        <NotificationsDropdown />
        <ThemeToggle />
        <UserMenu />
        <HelpLink />
        </div>
      </div>
    </header>
  )
}
