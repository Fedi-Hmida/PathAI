import { Button, Panel, StatusBadge, TextArea } from "@/components/ui";
import type { AssessmentQuestion } from "@/lib/api/assessment";

import styles from "./Assessment.module.css";

type AssessmentQuestionCardProps = {
  answer: string;
  disabled?: boolean;
  isSubmitting?: boolean;
  onAnswerChange: (answer: string) => void;
  onSubmit: () => void;
  question: AssessmentQuestion | null;
};

export function AssessmentQuestionCard({
  answer,
  disabled = false,
  isSubmitting = false,
  onAnswerChange,
  onSubmit,
  question
}: AssessmentQuestionCardProps) {
  if (!question) {
    return (
      <Panel
        description="Start the assessment to receive the first diagnostic question."
        title="Current Question"
      >
        <span className={styles.empty}>No active question yet.</span>
      </Panel>
    );
  }

  const canSubmit = !disabled && !isSubmitting;

  return (
    <Panel title="Current Question" elevated>
      <div className={styles.stack}>
        <div className={styles.questionHeader}>
          <div className={styles.questionTitle}>
            <div className={styles.chipRow}>
              <StatusBadge tone="info">{question.topic}</StatusBadge>
              <StatusBadge tone="neutral">{question.difficulty}</StatusBadge>
              <StatusBadge tone="neutral">{question.source.replace("_", " ")}</StatusBadge>
            </div>
            <h3>{question.question_type.replace("_", " ")}</h3>
          </div>
        </div>

        <p className={styles.prompt}>{question.prompt}</p>

        {question.expected_concepts.length > 0 ? (
          <div className={styles.stack}>
            <span className={styles.metricLabel}>Expected concepts</span>
            <div className={styles.chipRow}>
              {question.expected_concepts.map((concept) => (
                <span className={styles.chip} key={concept}>
                  {concept}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        <TextArea
          disabled={disabled || isSubmitting}
          hint="You can answer partially. Use 'I don't know' if this is a gap."
          label="Your answer"
          onChange={(event) => onAnswerChange(event.target.value)}
          rows={7}
          value={answer}
        />

        <div className={styles.buttonRow}>
          <Button disabled={!canSubmit} isLoading={isSubmitting} onClick={onSubmit}>
            Submit Answer
          </Button>
          <Button
            disabled={disabled || isSubmitting}
            onClick={() => onAnswerChange("I don't know")}
            variant="secondary"
          >
            I do not know
          </Button>
        </div>
      </div>
    </Panel>
  );
}
