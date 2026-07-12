import { useEffect, useState } from "react"

import { useNavigate } from "@tanstack/react-router"
import {
  Activity,
  AlertCircle,
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
  Inbox,
  MessageSquare,
  PhoneCall,
  ShieldCheck,
  Tag,
  UserCog,
  Users,
} from "lucide-react"

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"

type NavEntry = {
  to: string
  label: string
  icon: React.ElementType
  group: string
}

const NAV_ITEMS: ReadonlyArray<NavEntry> = [
  { to: "/", label: "Home", icon: Home, group: "Quick" },
  { to: "/inbox", label: "Inbox", icon: Inbox, group: "Quick" },
  { to: "/at-risk", label: "At Risk", icon: AlertCircle, group: "Quick" },
  { to: "/clients", label: "Clients", icon: Building2, group: "Navigate" },
  { to: "/persons", label: "Persons", icon: Users, group: "Navigate" },
  { to: "/service-sessions", label: "Sessions", icon: Calendar, group: "Navigate" },
  { to: "/care-callbacks", label: "Campaigns", icon: PhoneCall, group: "Navigate" },
  { to: "/care-callbacks/worklist", label: "My Worklist", icon: Headphones, group: "Navigate" },
  { to: "/surveys", label: "Surveys", icon: MessageSquare, group: "Navigate" },
  { to: "/engagements", label: "Engagements", icon: Handshake, group: "Navigate" },
  { to: "/contracts", label: "Contracts", icon: FileSignature, group: "Navigate" },
  { to: "/service-assignments", label: "Assignments", icon: FileCheck, group: "Navigate" },
  { to: "/services", label: "Services", icon: Briefcase, group: "Navigate" },
  { to: "/documents", label: "Documents", icon: FolderOpen, group: "Navigate" },
  { to: "/industries", label: "Industries", icon: BarChart3, group: "Settings" },
  { to: "/tags", label: "Tags", icon: Tag, group: "Settings" },
  { to: "/users", label: "Platform Users", icon: UserCog, group: "Settings" },
  { to: "/audit", label: "Audits", icon: ClipboardCheck, group: "Settings" },
  { to: "/activities", label: "Activity Logs", icon: Activity, group: "Settings" },
  { to: "/tenants", label: "Tenants", icon: ShieldCheck, group: "Settings" },
]

const TOGGLE_EVENT = "toggle-command-palette"

export function openCommandPalette() {
  window.dispatchEvent(new Event(TOGGLE_EVENT))
}

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault()
        setOpen((v) => !v)
      }
    }
    const onEvent = () => setOpen((v) => !v)
    window.addEventListener("keydown", onKey)
    window.addEventListener(TOGGLE_EVENT, onEvent as EventListener)
    return () => {
      window.removeEventListener("keydown", onKey)
      window.removeEventListener(TOGGLE_EVENT, onEvent as EventListener)
    }
  }, [])

  const grouped = NAV_ITEMS.reduce<Record<string, NavEntry[]>>((acc, item) => {
    ;(acc[item.group] ??= []).push(item)
    return acc
  }, {})

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Go to…" />
      <CommandList>
        <CommandEmpty>No results.</CommandEmpty>
        {Object.entries(grouped).map(([group, items]) => (
          <CommandGroup key={group} heading={group}>
            {items.map((item) => (
              <CommandItem
                key={item.to}
                value={item.label}
                onSelect={() => {
                  setOpen(false)
                  void navigate({ to: item.to })
                }}
              >
                <item.icon />
                {item.label}
              </CommandItem>
            ))}
          </CommandGroup>
        ))}
      </CommandList>
    </CommandDialog>
  )
}
