import { useState } from "react"

import { Copy, MoreHorizontal, UserPlus } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

export type InviteRole = "owner" | "editor" | "viewer"

export interface InviteMember {
  id: string
  name: string
  email: string
  role: InviteRole
  initials?: string
}

interface InviteToProjectCardProps {
  members?: ReadonlyArray<InviteMember>
  inviteLink?: string
  className?: string
}

const DEFAULT_MEMBERS: ReadonlyArray<InviteMember> = [
  {
    id: "u1",
    name: "Lynel",
    email: "lynel@example.com",
    role: "owner",
    initials: "L",
  },
  {
    id: "u2",
    name: "Karn",
    email: "karn@example.com",
    role: "editor",
    initials: "K",
  },
  {
    id: "u3",
    name: "Khateeb",
    email: "khateeb@example.com",
    role: "viewer",
    initials: "Kh",
  },
]

const ROLE_LABEL: Record<InviteRole, string> = {
  owner: "Owner",
  editor: "Can edit",
  viewer: "Can view",
}

export function InviteToProjectCard({
  members = DEFAULT_MEMBERS,
  inviteLink = "https://evexia.app/invite/Q4TF-93EA",
  className,
}: InviteToProjectCardProps = {}) {
  const [email, setEmail] = useState("")
  const [copied, setCopied] = useState(false)

  return (
    <Card className={cn("rounded-md", className)}>
      <CardHeader className="flex-row items-start gap-3 space-y-0 border-b border-border-subtle p-4">
        <span
          className="grid size-9 shrink-0 place-items-center rounded-md border border-dashed border-border bg-surface text-fg-muted"
          aria-hidden
        >
          <UserPlus className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <CardTitle className="text-sm font-semibold text-fg">
            Invite to tenant
          </CardTitle>
          <p className="mt-0.5 text-xs text-fg-muted">
            Add team members to collaborate on this tenant.
          </p>
        </div>
      </CardHeader>

      <CardContent className="grid gap-3 p-4">
        <div className="flex gap-2">
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email address"
            aria-label="Invite email address"
          />
          <Button disabled={email.trim().length === 0}>Invite</Button>
        </div>

        <div className="flex items-center gap-2 rounded-sm border border-border-subtle bg-surface px-2 py-1.5">
          <span className="min-w-0 flex-1 truncate font-mono text-xs text-fg-muted">
            {inviteLink}
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 px-2"
            onClick={() => {
              if (typeof navigator !== "undefined") {
                navigator.clipboard?.writeText(inviteLink).catch(() => {})
              }
              setCopied(true)
              setTimeout(() => setCopied(false), 1500)
            }}
          >
            <Copy className="size-3.5" />
            {copied ? "Copied" : "Copy"}
          </Button>
        </div>

        <ul className="grid gap-1.5">
          {members.map((m) => (
            <li
              key={m.id}
              className="flex items-center gap-3 rounded-sm border border-border-subtle bg-surface px-2 py-1.5"
            >
              <span
                className="grid size-7 shrink-0 place-items-center rounded-sm bg-muted font-mono text-xs font-medium text-fg-muted"
                aria-hidden
              >
                {m.initials ?? m.name.slice(0, 1).toUpperCase()}
              </span>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-fg">{m.name}</div>
                <div className="truncate text-xs text-fg-muted">{m.email}</div>
              </div>
              <Badge variant="outline" size="sm" className="shrink-0">
                {ROLE_LABEL[m.role]}
              </Badge>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-7"
                    aria-label={`Member options for ${m.name}`}
                  >
                    <MoreHorizontal className="size-3.5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem>Change role</DropdownMenuItem>
                  <DropdownMenuItem>Remove</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
