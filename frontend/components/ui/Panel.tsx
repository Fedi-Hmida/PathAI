import type { HTMLAttributes, ReactNode } from "react";

import { classNames } from "./classNames";
import styles from "./ui.module.css";

type PanelProps = HTMLAttributes<HTMLElement> & {
  actions?: ReactNode;
  children: ReactNode;
  description?: string;
  elevated?: boolean;
  title?: string;
};

export function Panel({
  actions,
  children,
  className,
  description,
  elevated = false,
  title,
  ...props
}: PanelProps) {
  return (
    <section
      className={classNames(styles.panel, elevated && styles.panelElevated, className)}
      {...props}
    >
      {title || description || actions ? (
        <header className={styles.panelHeader}>
          <div>
            {title ? <h2 className={styles.panelTitle}>{title}</h2> : null}
            {description ? <p className={styles.panelDescription}>{description}</p> : null}
          </div>
          {actions}
        </header>
      ) : null}
      <div className={styles.panelBody}>{children}</div>
    </section>
  );
}
