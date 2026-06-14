import { classNames } from "@/components/ui/classNames";
import type { PipelineStatusItem } from "@/lib/dashboard/types";

import styles from "./CommandCenterDashboard.module.css";

type PipelineStatusStripProps = {
  items: PipelineStatusItem[];
};

const toneClass: Record<PipelineStatusItem["tone"], string> = {
  idle: styles.pipelineToneIdle,
  running: styles.pipelineToneRunning,
  success: styles.pipelineToneSuccess,
  warning: styles.pipelineToneWarning
};

export function PipelineStatusStrip({ items }: PipelineStatusStripProps) {
  return (
    <section className={styles.pipelineStrip} aria-label="Pipeline status summary">
      {items.map((item) => (
        <div className={styles.pipelineStripItem} key={item.label}>
          <span className={classNames(styles.pipelineStatusDot, toneClass[item.tone])} />
          <div>
            <strong>{item.label}</strong>
            <span>{item.state}</span>
          </div>
        </div>
      ))}
    </section>
  );
}
