import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const statusPillVariants = cva(
  "inline-flex w-fit shrink-0 items-center justify-center gap-1 overflow-hidden rounded-full border border-transparent px-3 py-1.5 text-sm font-medium whitespace-nowrap",
  {
    variants: {
      tone: {
        neutral: "bg-surface-sunken text-tertiary",
        success: "bg-success-tint text-success",
        warning: "bg-warning-tint text-warning",
        danger: "bg-danger-tint text-danger",
        brand: "bg-brand-tint text-brand",
      },
    },
    defaultVariants: {
      tone: "neutral",
    },
  }
)

function StatusPill({
  className,
  tone,
  ...props
}: React.ComponentProps<"span"> & VariantProps<typeof statusPillVariants>) {
  return (
    <span
      data-slot="status-pill"
      data-tone={tone}
      className={cn(statusPillVariants({ tone }), className)}
      {...props}
    />
  )
}

export { StatusPill, statusPillVariants }
