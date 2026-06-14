import { Panel, StatusBadge } from "@/components/ui";
import type { AssessmentProgress, AssessmentSession } from "@/lib/api/assessment";

import styles from "./Assessment.module.css";

type AssessmentProgressPanelProps = {
  progress?: AssessmentProgress | null;
  session?: AssessmentSession | null;
};

export function AssessmentProgressPanel({ progress, session }: AssessmentProgressPanelProps) {
  return (
    <Panel
      description="Progress updates after every submitted answer. Confidence is evidence-based, not a promise of correctness."
      title="Assessment Progress"
    >
      {progress ? (
        <div className={styles.stack}>
          <div className={styles.progressGrid}>
            <Metric
              label="Answered"
              value={`${progress.answered_count}/${progress.max_questions}`}
            />
            <Metric label="Asked" value={String(progress.asked_count)} />
            <Metric label="Difficulty" value={progress.current_difficulty} />
            <Metric label="Status" value={progress.status.replace("_", " ")} />
          </div>
          <div className={styles.stack}>
            <div className={styles.feedbackHeader}>
              <span className={styles.metricLabel}>Confidence</span>
              <StatusBadge tone={progress.enough_evidence ? "success" : "warning"}>
                {Math.round(progress.confidence_score * 100)}%
              </StatusBadge>
            </div>
            <div className={styles.bar} aria-hidden="true">
              <div
                className={styles.barFill}
                style={{ width: `${Math.round(progress.confidence_score * 100)}%` }}
              />
            </div>
            <p className={styles.hint}>
              Enough evidence: {progress.enough_evidence ? "yes" : "not yet"}.
              {session ? ` Session ${session.session_id.slice(0, 8)} is stored in memory.` : ""}
            </p>
          </div>
        </div>
      ) : (
        <span className={styles.empty}>Start the assessment to see progress.</span>
      )}
    </Panel>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.metric}>
      <span className={styles.metricLabel}>{label}</span>
      <strong className={styles.metricValue}>{value}</strong>
    </div>
  );
}
