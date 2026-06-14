import type { ReactNode } from "react";

import styles from "./ui.module.css";

type EmptyStateProps = {
  action?: ReactNode;
  message?: string;
  title?: string;
};

export function EmptyState({
  action,
  message = "Run the workflow to populate this section.",
  title = "No data yet"
}: EmptyStateProps) {
  return (
    <div className={styles.state}>
      <div className={styles.stateContent}>
        <h2 className={styles.stateTitle}>{title}</h2>
        <p className={styles.stateMessage}>{message}</p>
        {action}
      </div>
    </div>
  );
}
