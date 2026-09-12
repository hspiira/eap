import * as React from "react"

import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/**
 * Pill buttons, matching the landing page.
 *
 * Three filled weights, and which one to reach for is a rule, not a taste:
 *
 * - `default` is near-black. Every ordinary action: toolbars, table rows,
 *   dialogs, anything a person does many times a screen. A brand-coloured
 *   button on every row makes the brand shout where it means nothing.
 * - `primary` is the brand. **At most one per page**, for the action the page
 *   exists to offer: the create button in a page header, a form's submit.
 * - `highlight` is the one saturated fill, rarer still. Its colour sits at
 *   1.16:1 on white, so it can never be text, a border, an icon or a chart
 *   stroke; it works only as a block with near-black type on it.
 *
 * The brand also keeps links, active nav, selected rows and focus rings, so
 * dropping it from ordinary buttons quietens it rather than removing it.
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-action text-action-fg hover:bg-action/90",
        primary: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        highlight: "bg-highlight text-highlight-fg hover:bg-highlight/90",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "rounded-none text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-10 px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
    )
  },
)
Button.displayName = "Button"

export { Button, buttonVariants }
