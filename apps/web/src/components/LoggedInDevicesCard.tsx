import { Globe, Laptop, Smartphone } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

type DeviceType = "desktop" | "mobile" | "browser"

export interface ActiveSession {
  id: string
  device: DeviceType
  label: string
  location?: string
  lastActive: string
  current?: boolean
}

interface LoggedInDevicesCardProps {
  sessions?: ReadonlyArray<ActiveSession>
  className?: string
}

const DEVICE_ICON: Record<DeviceType, React.ElementType> = {
  desktop: Laptop,
  mobile: Smartphone,
  browser: Globe,
}

const DEFAULT_SESSIONS: ReadonlyArray<ActiveSession> = [
  {
    id: "s1",
    device: "desktop",
    label: "MacBook Pro · Safari",
    location: "Nairobi, KE",
    lastActive: "Active now",
    current: true,
  },
  {
    id: "s2",
    device: "mobile",
    label: "iPhone · Mobile app",
    location: "Nairobi, KE",
    lastActive: "2h ago",
  },
  {
    id: "s3",
    device: "browser",
    label: "Chrome · Windows",
    location: "Mombasa, KE",
    lastActive: "3d ago",
  },
]

export function LoggedInDevicesCard({
  sessions = DEFAULT_SESSIONS,
  className,
}: LoggedInDevicesCardProps = {}) {
  return (
    <Card className={cn("rounded-md", className)}>
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 border-b border-border-subtle p-3">
        <CardTitle className="text-sm font-semibold text-fg">
          Active sessions
        </CardTitle>
        <Badge variant="secondary" size="sm" className="font-mono tabular-nums">
          {sessions.length}
        </Badge>
      </CardHeader>
      <CardContent className="p-0">
        <ul className="divide-y divide-border-subtle">
          {sessions.map((s) => {
            const Icon = DEVICE_ICON[s.device]
            return (
              <li key={s.id} className="flex items-center gap-3 p-3">
                <span
                  className="grid size-8 shrink-0 place-items-center rounded-md bg-muted text-fg-muted"
                  aria-hidden
                >
                  <Icon className="size-4" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium text-fg">
                      {s.label}
                    </span>
                    {s.current ? (
                      <Badge variant="secondary" size="sm" className="text-success">
                        Current
                      </Badge>
                    ) : null}
                  </div>
                  <div className="text-xs text-fg-muted">
                    {s.location ? `${s.location} · ` : ""}
                    <span className="font-mono tabular-nums">
                      {s.lastActive}
                    </span>
                  </div>
                </div>
                {!s.current ? (
                  <Button variant="outline" size="sm">
                    Sign out
                  </Button>
                ) : null}
              </li>
            )
          })}
        </ul>
      </CardContent>
    </Card>
  )
}
