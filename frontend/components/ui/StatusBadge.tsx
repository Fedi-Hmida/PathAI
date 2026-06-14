import type { HTMLAttributes, ReactNode } from "react";

import { classNames } from "./classNames";
import styles from "./ui.module.css";

export type StatusTone = "neutral" | "success" | "warning" | "danger" | "info";

type StatusBadgeProps = HTMLAttributes<HTMLSpanElement> & {
  children: ReactNode;
  tone?: StatusTone;
};

const toneClass: Record<StatusTone, string> = {
  neutral: styles.badgeNeutral,
  success: styles.badgeSuccess,
  warning: styles.badgeWarning,
  danger: styles.badgeDanger,
  info: styles.badgeInfo
};

export function StatusBadge({
  children,
  className,
  tone = "neutral",
  ...props
}: StatusBadgeProps) {
  return (
    <span className={classNames(styles.badge, toneClass[tone], className)} {...props}>
      {children}
    </span>
  );
}
