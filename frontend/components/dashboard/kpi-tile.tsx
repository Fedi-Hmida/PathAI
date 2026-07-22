import Link from "next/link";
import type { LucideIcon } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type KpiTone = "neutral" | "success" | "warning" | "danger";

const TONE_TEXT: Record<KpiTone, string> = {
  neutral: "text-tertiary",
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
};

type KpiTileProps = {
  label: string;
  value: string;
  statusText?: string;
  tone?: KpiTone;
  icon?: LucideIcon;
  href?: string;
};

export function KpiTile({ label, value, statusText, tone = "neutral", icon: Icon, href }: KpiTileProps) {
  const content = (
    <Card className={cn("gap-2 py-5 px-5", href ? "transition-colors hover:bg-surface-sunken" : null)}>
      <div className="flex items-center justify-between">
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          {label}
        </span>
        {Icon ? <Icon className={cn("size-4", TONE_TEXT[tone])} /> : null}
      </div>
      <div className="font-tabular text-[30px] leading-tight font-semibold text-foreground">
        {value}
      </div>
      {statusText ? (
        <div className={cn("text-xs font-semibold", TONE_TEXT[tone])}>{statusText}</div>
      ) : null}
    </Card>
  );

  return href ? <Link href={href}>{content}</Link> : content;
}
