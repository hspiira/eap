import { cn } from "@/lib/utils"

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div // Neutral: a loading placeholder is absence, not state, and a brand-tinted
      // shimmer puts colour on every screen before it has anything to say.
      className={cn("animate-pulse rounded-md bg-fg/8", className)}
      {...props}
    />
  )
}

export { Skeleton }
