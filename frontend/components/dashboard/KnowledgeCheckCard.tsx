import { classNames } from "@/components/ui/classNames";
import type { QuizOption } from "@/lib/dashboard/types";

import styles from "./CommandCenterDashboard.module.css";

type KnowledgeCheckCardProps = {
  eyebrow: string;
  options: QuizOption[];
  question: string;
};

export function KnowledgeCheckCard({ eyebrow, options, question }: KnowledgeCheckCardProps) {
  return (
    <section className={styles.quiz} aria-labelledby="knowledge-check-title">
      <header className={styles.quizHeader}>
        <div>
          <h2 id="knowledge-check-title">Knowledge Check</h2>
          <span>{eyebrow}</span>
        </div>
        <div className={styles.quizDots} aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      </header>
      <div className={styles.quizBody}>
        <p className={styles.quizQuestion}>{question}</p>
        <div className={styles.quizOptions} aria-label="Quiz options preview">
          {options.map((option) => (
            <button
              className={classNames(styles.quizOption, option.correct && styles.quizOptionCorrect)}
              key={option.label}
              type="button"
            >
              <span>
                {option.label}. {option.text}
              </span>
              {option.correct ? <strong aria-label="Selected correct option">OK</strong> : null}
            </button>
          ))}
        </div>
        <div className={styles.quizActions}>
          <button className={styles.quizPrimary} type="button">
            Submit Response
          </button>
          <button className={styles.quizSecondary} type="button">
            Hint
          </button>
        </div>
      </div>
    </section>
  );
}
