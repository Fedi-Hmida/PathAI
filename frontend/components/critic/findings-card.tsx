import type { LucideIcon } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface FindingsCardProps {
  eyebrow?: string;
  title: string;
  titleClassName?: string;
  items: string[];
  icon: LucideIcon;
  iconClassName: string;
  emptyMessage: string;
}

export function FindingsCard({
  eyebrow,
  title,
  titleClassName,
  items,
  icon: Icon,
  iconClassName,
  emptyMessage,
}: FindingsCardProps) {
  return (
    <Card className="min-w-70 flex-1">
      <CardHeader>
        {eyebrow ? (
          <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
            {eyebrow}
          </span>
        ) : null}
        <CardTitle className={titleClassName}>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length > 0 ? (
          <ul className="flex flex-col gap-3">
            {items.map((item) => (
              <li
                key={item}
                className="text-foreground flex items-start gap-2.5 text-sm leading-relaxed"
              >
                <Icon className={cn("mt-0.5 size-4 flex-none", iconClassName)} />
                {item}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-muted-foreground text-sm">{emptyMessage}</p>
        )}
      </CardContent>
    </Card>
  );
}
