import * as React from "react"

import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
} from "@/components/ui/sheet"
import { cn } from "@/lib/utils"

type SheetSize = "sm" | "md" | "lg" | "xl"

const SIZE_CLASS: Record<SheetSize, string> = {
  sm: "sm:max-w-sm",
  md: "sm:max-w-md",
  lg: "sm:max-w-lg",
  xl: "sm:max-w-xl",
}

interface SheetFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: React.ReactNode
  size?: SheetSize
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void | Promise<void>
  isSubmitting?: boolean
  serverError?: string
  submitLabel?: string
  submittingLabel?: string
  cancelLabel?: string
  destructive?: boolean
  children: React.ReactNode
}

export function SheetForm({
  open,
  onOpenChange,
  title,
  description,
  size = "md",
  onSubmit,
  isSubmitting = false,
  serverError,
  submitLabel = "Save",
  submittingLabel = "Saving…",
  cancelLabel = "Cancel",
  destructive = false,
  children,
}: SheetFormProps) {
  const formRef = React.useRef<HTMLFormElement>(null)
  const bodyRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    if (!open) return
    const t = setTimeout(() => {
      const first = bodyRef.current?.querySelector<HTMLElement>(
        "input:not([type=hidden]):not([disabled]),select:not([disabled]),textarea:not([disabled])",
      )
      first?.focus()
    }, 80)
    return () => clearTimeout(t)
  }, [open])

  const onKeyDown: React.KeyboardEventHandler<HTMLFormElement> = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault()
      formRef.current?.requestSubmit()
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className={cn(
          "flex h-full w-full flex-col gap-0 rounded-none border-l border-fg/15 bg-bg p-0 shadow-xl",
          SIZE_CLASS[size],
        )}
      >
        <header className="flex shrink-0 items-start gap-4 border-b border-fg/10 px-5 py-4 pr-12">
          <div className="min-w-0 flex-1">
            <SheetTitle className="text-base font-semibold leading-tight text-fg">
              {title}
            </SheetTitle>
            {description ? (
              <SheetDescription className="mt-1 text-xs leading-relaxed text-fg/60">
                {description}
              </SheetDescription>
            ) : null}
          </div>
        </header>

        <form
          ref={formRef}
          onSubmit={onSubmit}
          onKeyDown={onKeyDown}
          noValidate
          className="flex min-h-0 flex-1 flex-col"
        >
          <div ref={bodyRef} className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
            {serverError ? (
              <div
                role="alert"
                className="mb-4 rounded-sm border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger-fg"
              >
                {serverError}
              </div>
            ) : null}
            <div className="space-y-6">{children}</div>
          </div>

          <footer className="flex shrink-0 items-center justify-between gap-3 border-t border-fg/10 bg-surface px-5 py-3">
            <span className="hidden text-[11px] text-fg/45 sm:inline">
              <kbd className="rounded-sm border border-fg/15 bg-bg px-1 py-px font-mono text-[10px] text-fg/55">
                ⌘ Enter
              </kbd>{" "}
              to save
            </span>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
              >
                {cancelLabel}
              </Button>
              <Button
                type="submit"
                size="sm"
                variant={destructive ? "destructive" : "default"}
                disabled={isSubmitting}
                className="min-w-[6.5rem]"
              >
                {isSubmitting ? submittingLabel : submitLabel}
              </Button>
            </div>
          </footer>
        </form>
      </SheetContent>
    </Sheet>
  )
}
