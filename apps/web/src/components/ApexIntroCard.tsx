import { Mic, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface ApexIntroCardProps {
  className?: string
}

export function ApexIntroCard({ className }: ApexIntroCardProps = {}) {
  return (
    <Card className={cn("rounded-md", className)}>
      <CardContent className="grid gap-3 p-4">
        <div className="flex items-start gap-3">
          <span
            className="grid size-10 shrink-0 place-items-center rounded-md bg-primary/10 text-primary"
            aria-hidden
          >
            <Sparkles className="size-5" />
          </span>
          <div className="min-w-0 flex-1 grid gap-1">
            <p className="text-sm text-fg">
              Hello, I'm <strong className="font-semibold">Apex</strong> — your
              tenant assistant.
            </p>
            <p className="text-sm text-fg-muted">
              Ask me anything about clients, contracts, sessions, or incidents.
              I'll surface the right record and the right action.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-sm border border-border-subtle bg-surface px-3 py-2">
          <span className="font-mono text-xs tabular-nums text-fg-subtle">
            0:00
          </span>
          <div
            className="flex flex-1 items-center justify-center gap-0.5"
            aria-hidden
          >
            {Array.from({ length: 32 }).map((_, i) => (
              <span
                key={i}
                className="w-0.5 shrink-0 rounded-full bg-primary/40"
                style={{
                  height: `${Math.max(4, 10 + Math.sin(i * 0.6) * 10)}px`,
                }}
              />
            ))}
          </div>
          <Button variant="outline" size="icon" aria-label="Start voice input">
            <Mic className="size-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
