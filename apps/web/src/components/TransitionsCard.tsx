import { useState } from "react"

import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Ban,
  Copy,
  Maximize2,
  MoveHorizontal,
  Plus,
  Send,
  Sparkles,
  Square,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

const TRANSITION_TYPES = [
  { id: "none", label: "None", icon: Ban },
  { id: "dissolve", label: "Dissolve", icon: Copy },
  { id: "push", label: "Push", icon: MoveHorizontal },
  { id: "slide", label: "Slide", icon: ArrowRight },
  { id: "scale", label: "Scale", icon: Maximize2 },
  { id: "fade", label: "Fade", icon: Square },
] as const

type TransitionId = (typeof TRANSITION_TYPES)[number]["id"]

const APPLY_OPTIONS = ["Both", "On Enter", "On Exit"] as const
type ApplyOption = (typeof APPLY_OPTIONS)[number]

const DIRECTIONS = [
  { id: "right", label: "Right", icon: ArrowRight },
  { id: "left", label: "Left", icon: ArrowLeft },
  { id: "up", label: "Up", icon: ArrowUp },
  { id: "down", label: "Down", icon: ArrowDown },
] as const

type DirectionId = (typeof DIRECTIONS)[number]["id"]

const QUICK_PROMPTS = [
  "Make it fast",
  "Smooth slide from top-left to bottom-right",
] as const

export function TransitionsCard() {
  const [transition, setTransition] = useState<TransitionId>("push")
  const [apply, setApply] = useState<ApplyOption>("Both")
  const [direction, setDirection] = useState<DirectionId>("right")
  const [prompt, setPrompt] = useState("")

  return (
    <Card className="rounded-md">
      <CardHeader className="flex-row items-center gap-2 space-y-0 border-b border-border-subtle p-3">
        <Sparkles className="size-4 text-primary" aria-hidden />
        <CardTitle className="text-sm font-semibold text-fg">
          Transitions
        </CardTitle>
      </CardHeader>

      <CardContent className="grid gap-4 p-4">
        <div className="flex flex-wrap items-center gap-2">
          {TRANSITION_TYPES.map(({ id, label, icon: Icon }) => {
            const selected = id === transition
            return (
              <Button
                key={id}
                type="button"
                variant="outline"
                size="sm"
                aria-pressed={selected}
                onClick={() => setTransition(id)}
                className={cn(
                  "h-auto gap-2 rounded-sm px-3 py-1.5 text-sm font-medium",
                  selected
                    ? "border-primary bg-primary/10 text-primary hover:bg-primary/15"
                    : "border-border-subtle bg-surface text-fg hover:bg-surface-hover",
                )}
              >
                <Icon className="size-3.5" />
                {label}
              </Button>
            )
          })}
          <Button
            variant="outline"
            size="icon"
            aria-label="More transitions"
            className="border-dashed text-fg-subtle"
          >
            <Plus className="size-3.5" />
          </Button>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div
            role="radiogroup"
            aria-label="Apply on"
            className="inline-flex rounded-sm border border-border-subtle bg-surface p-0.5"
          >
            {APPLY_OPTIONS.map((opt) => {
              const selected = opt === apply
              return (
                <Button
                  key={opt}
                  type="button"
                  variant="ghost"
                  size="sm"
                  role="radio"
                  aria-checked={selected}
                  onClick={() => setApply(opt)}
                  className={cn(
                    "h-auto rounded-sm px-2.5 py-1 text-xs font-medium",
                    selected
                      ? "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground"
                      : "text-fg-muted hover:bg-transparent hover:text-fg",
                  )}
                >
                  {opt}
                </Button>
              )
            })}
          </div>
          <div className="inline-flex rounded-sm border border-border-subtle bg-surface p-0.5">
            {DIRECTIONS.map(({ id, label, icon: Icon }) => {
              const selected = id === direction
              return (
                <Button
                  key={id}
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-pressed={selected}
                  aria-label={label}
                  onClick={() => setDirection(id)}
                  className={cn(
                    "size-7 rounded-sm",
                    selected
                      ? "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground"
                      : "text-fg-muted hover:bg-transparent hover:text-fg",
                  )}
                >
                  <Icon className="size-3.5" />
                </Button>
              )
            })}
          </div>
          <span className="text-xs text-fg-muted">Apply to all scenes</span>
        </div>

        <div className="grid gap-2 rounded-sm border border-border-subtle bg-surface p-3">
          <div className="flex flex-wrap gap-2">
            {QUICK_PROMPTS.map((p) => (
              <Button
                key={p}
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setPrompt(p)}
                className="h-auto rounded-sm border-border-subtle bg-bg px-2.5 py-1 text-xs text-fg-muted hover:bg-surface-hover hover:text-fg"
              >
                {p}
              </Button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <Input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe a transition…"
              aria-label="Transition prompt"
              className="flex-1 rounded-sm bg-bg"
            />
            <Button
              size="icon"
              aria-label="Submit prompt"
              disabled={prompt.trim().length === 0}
            >
              <Send className="size-3.5" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
