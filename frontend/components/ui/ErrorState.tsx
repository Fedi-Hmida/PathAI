import type { ReactNode } from "react";

import { StatusBadge } from "./StatusBadge";
import styles from "./ui.module.css";

type ErrorStateProps = {
  action?: ReactNode;
  message: string;
  title?: string;
};

export function ErrorState({ action, message, title = "Something went wrong" }: ErrorStateProps) {
  return (
    <div className={styles.state} role="alert">
      <div className={styles.stateContent}>
        <StatusBadge tone="danger">Error</StatusBadge>
        <h2 className={styles.stateTitle}>{title}</h2>
        <p className={styles.stateMessage}>{message}</p>
        {action}
      </div>
    </div>
  );
}
