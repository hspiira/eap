import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center font-medium rounded-none border",
  {
    variants: {
      variant: {
        default:
          "border-natural bg-natural text-white",
        secondary:
          "border-[#5A626A]/30 bg-[#f0f0f0] text-[#5A626A]",
        outline:
          "border-[#5A626A]/50 text-[#5A626A] bg-transparent",
      },
      size: {
        sm: "px-1.5 py-0 text-xs",
        default: "px-2 py-0.5 text-xs",
        lg: "px-2.5 py-1 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, size, ...props }: BadgeProps) {
  return (
    <div
      className={cn(badgeVariants({ variant, size }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
