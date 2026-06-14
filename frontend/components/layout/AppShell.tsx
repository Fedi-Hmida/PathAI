import type { ReactNode } from "react";

import styles from "./AppShell.module.css";
import { NavigationRail, type NavigationItemId } from "./NavigationRail";
import { TopStatusBar } from "./TopStatusBar";

type AppShellProps = {
  activeItem?: NavigationItemId;
  children: ReactNode;
  eyebrow?: string;
  statusSlot?: ReactNode;
  subtitle?: string;
  title?: string;
};

export function AppShell({
  activeItem = "demo",
  children,
  eyebrow = "PathAI",
  statusSlot = <TopStatusBar />,
  subtitle = "Local no-auth learning workflow",
  title = "Learning Command Center"
}: AppShellProps) {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.brand}>
            <p className={styles.eyebrow}>{eyebrow}</p>
            <h1 className={styles.title}>{title}</h1>
            <p className={styles.subtitle}>{subtitle}</p>
          </div>
          {statusSlot ? <div className={styles.statusSlot}>{statusSlot}</div> : null}
        </div>
      </header>
      <div className={styles.commandFrame}>
        <NavigationRail activeItem={activeItem} />
        <main className={styles.body}>{children}</main>
      </div>
    </div>
  );
}
