import styles from "./CommandCenterDashboard.module.css";

type NextAction = {
  action: string;
  detail: string;
  due: string;
  reason: string;
};

type LearningPathProgress = {
  completedWeeks: number;
  currentFocus: string;
  pace: string;
  progress: number;
  totalWeeks: number;
};

type CommandCenterSummaryCardsProps = {
  learningPath: LearningPathProgress;
  nextAction: NextAction;
};

export function CommandCenterSummaryCards({
  learningPath,
  nextAction
}: CommandCenterSummaryCardsProps) {
  return (
    <section className={styles.summaryGrid} aria-label="Dashboard priorities">
      <article className={styles.nextActionCard}>
        <div className={styles.summaryHeader}>
          <span className={styles.columnTitle}>Next action</span>
          <span className={styles.metaPill}>{nextAction.due}</span>
        </div>
        <h2>{nextAction.action}</h2>
        <p>{nextAction.detail}</p>
        <div className={styles.reasonBox}>
          <strong>Why now</strong>
          <span>{nextAction.reason}</span>
        </div>
      </article>

      <article className={styles.pathProgressCard}>
        <div className={styles.summaryHeader}>
          <span className={styles.columnTitle}>Learning path</span>
          <strong>
            {learningPath.completedWeeks}/{learningPath.totalWeeks} weeks
          </strong>
        </div>
        <div className={styles.pathProgressRow}>
          <span>{learningPath.progress}% complete</span>
          <span>{learningPath.pace}</span>
        </div>
        <div className={styles.progressTrack} aria-hidden="true">
          <div style={{ width: `${learningPath.progress}%` }} />
        </div>
        <p>
          Current focus: <strong>{learningPath.currentFocus}</strong>
        </p>
      </article>
    </section>
  );
}
