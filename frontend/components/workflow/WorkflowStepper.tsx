import { classNames } from "@/components/ui/classNames";

import styles from "./WorkflowStepper.module.css";

export type WorkflowStepStatus = "pending" | "running" | "done" | "failed" | "blocked";

export type WorkflowStep = {
  id: string;
  label: string;
  status: WorkflowStepStatus;
};

export const pathaiWorkflowSteps: WorkflowStep[] = [
  { id: "assessment", label: "Assessment", status: "pending" },
  { id: "knowledge-map", label: "Knowledge Map", status: "pending" },
  { id: "curriculum", label: "Curriculum", status: "pending" },
  { id: "resources", label: "Resources", status: "pending" },
  { id: "critic", label: "Critic", status: "pending" },
  { id: "progress", label: "Progress", status: "pending" },
  { id: "quiz", label: "Quiz", status: "pending" },
  { id: "adapter", label: "Adapter", status: "pending" },
  { id: "evaluation", label: "Evaluation", status: "pending" },
  { id: "orchestration", label: "Orchestration", status: "pending" }
];

type WorkflowStepperProps = {
  description?: string;
  steps?: WorkflowStep[];
  title?: string;
  variant?: "compact" | "full";
};

const statusLabel: Record<WorkflowStepStatus, string> = {
  blocked: "Blocked",
  done: "Done",
  failed: "Failed",
  pending: "Pending",
  running: "Running"
};

export function WorkflowStepper({
  description = "PathAI execution path from learner diagnosis to evaluation.",
  steps = pathaiWorkflowSteps,
  title = "Agent workflow",
  variant = "compact"
}: WorkflowStepperProps) {
  return (
    <section aria-label={title} className={styles.stepper}>
      <header className={styles.header}>
        <div>
          <h2 className={styles.title}>{title}</h2>
          <p className={styles.description}>{description}</p>
        </div>
      </header>
      <ol className={classNames(styles.list, variant === "compact" ? styles.compact : styles.full)}>
        {steps.map((step, index) => (
          <li
            aria-label={`${step.label}: ${statusLabel[step.status]}`}
            className={classNames(styles.step, styles[step.status])}
            key={step.id}
          >
            <span aria-hidden="true" className={styles.index}>
              {index + 1}
            </span>
            <span className={styles.label}>{step.label}</span>
            <span className={styles.status}>{statusLabel[step.status]}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
