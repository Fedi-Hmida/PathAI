import { classNames } from "@/components/ui/classNames";
import type { SystemHealthMetric } from "@/lib/dashboard/types";

import styles from "./CommandCenterDashboard.module.css";

type SystemHealthPanelProps = {
  metrics: SystemHealthMetric[];
};

const toneClass: Record<SystemHealthMetric["tone"], string> = {
  info: styles.healthToneInfo,
  success: styles.healthToneSuccess,
  warning: styles.healthToneWarning
};

export function SystemHealthPanel({ metrics }: SystemHealthPanelProps) {
  return (
    <section className={styles.inspectorSection} aria-labelledby="system-health-title">
      <h2 className={styles.inspectorTitle} id="system-health-title">
        System Health
      </h2>
      <div className={styles.healthGrid}>
        {metrics.map((metric) => (
          <article className={styles.healthMetric} key={metric.label}>
            <span className={classNames(styles.healthDot, toneClass[metric.tone])} />
            <strong>{metric.value}</strong>
            <span>{metric.label}</span>
            <small>{metric.detail}</small>
          </article>
        ))}
      </div>
    </section>
  );
}
