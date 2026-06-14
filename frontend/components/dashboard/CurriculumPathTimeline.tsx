import { classNames } from "@/components/ui/classNames";
import type { CurriculumWeek } from "@/lib/dashboard/types";

import styles from "./CommandCenterDashboard.module.css";

type CurriculumPathTimelineProps = {
  weeks: CurriculumWeek[];
};

const weekStatusClass: Record<CurriculumWeek["status"], string> = {
  completed: styles.weekCompleted,
  current: styles.weekCurrent,
  locked: styles.weekLocked,
  milestone: styles.weekMilestone
};

export function CurriculumPathTimeline({ weeks }: CurriculumPathTimelineProps) {
  return (
    <section className={styles.timeline} aria-labelledby="curriculum-path-title">
      <header className={styles.cardHeader}>
        <h2 className={styles.cardTitle} id="curriculum-path-title">
          <span aria-hidden="true">Route</span>
          Curriculum Path
        </h2>
        <div className={styles.miniLegend} aria-label="Timeline legend">
          <span>
            <i className={styles.legendDot} aria-hidden="true" />
            Completed
          </span>
          <span>
            <i className={classNames(styles.legendDot, styles.legendDotBlue)} aria-hidden="true" />
            In progress
          </span>
        </div>
      </header>
      <div className={styles.timelineBody}>
        <div className={styles.timelineLine} aria-hidden="true" />
        <div className={styles.weekGrid}>
          {weeks.map((week) => (
            <article className={classNames(styles.weekCard, weekStatusClass[week.status])} key={week.week}>
              <div>
                <div className={styles.weekNode}>{week.week}</div>
                <h3>{week.focus}</h3>
                <span>{week.label}</span>
              </div>
              <p className={styles.weekDetail}>{week.detail}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
