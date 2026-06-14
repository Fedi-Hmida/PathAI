import { Panel, StatusBadge } from "@/components/ui";
import type { AnswerEvaluation } from "@/lib/api/assessment";

import styles from "./Assessment.module.css";

type AnswerFeedbackPanelProps = {
  evaluation: AnswerEvaluation | null;
};

export function AnswerFeedbackPanel({ evaluation }: AnswerFeedbackPanelProps) {
  return (
    <Panel
      description="The backend rubric checks concept coverage and treats uncertainty as useful evidence."
      title="Answer Feedback"
    >
      {evaluation ? (
        <div className={styles.feedbackGrid}>
          <div className={styles.feedbackHeader}>
            <StatusBadge tone={toneForSignal(evaluation.signal)}>{evaluation.signal}</StatusBadge>
            <strong>Score {Math.round(evaluation.score * 100)}%</strong>
          </div>
          <p className={styles.feedbackText}>{evaluation.feedback}</p>
          <div className={styles.conceptGrid}>
            <ConceptList label="Matched concepts" items={evaluation.matched_concepts} />
            <ConceptList label="Missing concepts" items={evaluation.missing_concepts} />
          </div>
        </div>
      ) : (
        <span className={styles.empty}>Submit an answer to receive feedback.</span>
      )}
    </Panel>
  );
}

function ConceptList({ items, label }: { items: string[]; label: string }) {
  return (
    <div className={styles.stack}>
      <span className={styles.metricLabel}>{label}</span>
      <div className={styles.chipRow}>
        {items.length > 0 ? (
          items.map((item) => (
            <span className={styles.chip} key={`${label}-${item}`}>
              {item}
            </span>
          ))
        ) : (
          <span className={styles.empty}>None</span>
        )}
      </div>
    </div>
  );
}

function toneForSignal(signal: AnswerEvaluation["signal"]) {
  if (signal === "strong") {
    return "success";
  }
  if (signal === "missing") {
    return "danger";
  }
  return "warning";
}
