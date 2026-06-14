import type { CriticIssue } from "@/lib/dashboard/types";

import styles from "./CommandCenterDashboard.module.css";

type CriticAnalysisPanelProps = {
  decision: string;
  issues: CriticIssue[];
  score: number;
};

export function CriticAnalysisPanel({ decision, issues, score }: CriticAnalysisPanelProps) {
  const scorePercent = Math.round(score * 100);

  return (
    <section className={styles.inspectorSection} aria-labelledby="critic-analysis-title">
      <div className={styles.inspectorTitleRow}>
        <h2 className={styles.inspectorTitle} id="critic-analysis-title">
          Critic Analysis
        </h2>
        <span className={styles.dangerChip}>{decision}</span>
      </div>
      <div className={styles.scoreRow}>
        <span className={styles.scoreValue}>
          {score.toFixed(2)}
          <span> / 1.00</span>
        </span>
        <span className={styles.scoreLabel}>Critical path score</span>
      </div>
      <div className={styles.scoreTrack} aria-hidden="true">
        <div className={styles.scoreFill} style={{ width: `${scorePercent}%` }} />
      </div>
      <div className={styles.issueList}>
        {issues.map((issue) => (
          <article className={styles.issueCard} key={issue.title}>
            <span className={styles.issueMark} aria-hidden="true">
              X
            </span>
            <div>
              <h3>{issue.title}</h3>
              <p>{issue.detail}</p>
              <div className={styles.issueSolution}>
                <strong>Proposed correction</strong>
                <span>{issue.solution}</span>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
