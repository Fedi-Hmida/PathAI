"use client";

import { useMemo, useState } from "react";

import { Button, ErrorState, StatusBadge } from "@/components/ui";
import { WorkflowStepper, pathaiWorkflowSteps, type WorkflowStep } from "@/components/workflow";
import {
  finalizeAssessment,
  startAssessment,
  submitAssessmentAnswer,
  type AnswerEvaluation,
  type AssessmentQuestion,
  type AssessmentSession,
  type FinalAssessmentResult
} from "@/lib/api/assessment";
import { PathAIFrontendApiError } from "@/lib/api/client";
import { updateDashboardRunState } from "@/lib/dashboard/runState";

import { AnswerFeedbackPanel } from "./AnswerFeedbackPanel";
import { AssessmentProgressPanel } from "./AssessmentProgressPanel";
import { AssessmentQuestionCard } from "./AssessmentQuestionCard";
import { GoalIntakeForm, type GoalIntakeFormValue } from "./GoalIntakeForm";
import { KnowledgeMapPreview } from "./KnowledgeMapPreview";
import styles from "./Assessment.module.css";

const initialFormValue: GoalIntakeFormValue = {
  goal: "Learn RAG systems for a graduation project",
  hours_per_week: 6,
  max_questions: 6,
  target_level: "intermediate",
  timeline_weeks: 4
};

export function AssessmentWorkspace() {
  const [formValue, setFormValue] = useState<GoalIntakeFormValue>(initialFormValue);
  const [session, setSession] = useState<AssessmentSession | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<AssessmentQuestion | null>(null);
  const [answer, setAnswer] = useState("");
  const [evaluation, setEvaluation] = useState<AnswerEvaluation | null>(null);
  const [result, setResult] = useState<FinalAssessmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isFinalizing, setIsFinalizing] = useState(false);

  const workflowSteps = useMemo(() => buildAssessmentSteps(session, result, error), [session, result, error]);
  const isCompleted = Boolean(result) || session?.status === "completed";
  const progress = result?.progress ?? session?.progress ?? null;
  const knowledgeMap = result?.knowledge_map ?? session?.knowledge_map ?? null;

  async function handleStartAssessment() {
    setError(null);
    setIsStarting(true);
    setEvaluation(null);
    setResult(null);
    setAnswer("");
    try {
      const response = await startAssessment({
        ...formValue,
        user_id: "demo-ui-user"
      });
      setSession(response.session);
      setCurrentQuestion(response.next_question);
      updateDashboardRunState({
        dataMode: "backend",
        sessionId: response.session.session_id
      });
    } catch (caught) {
      setError(toDisplayError(caught));
    } finally {
      setIsStarting(false);
    }
  }

  async function handleSubmitAnswer() {
    if (!session || isCompleted) {
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      const response = await submitAssessmentAnswer(session.session_id, answer);
      setSession(response.session);
      setEvaluation(response.evaluation);
      setResult(response.result);
      setCurrentQuestion(response.next_question);
      setAnswer("");
      updateDashboardRunState({
        dataMode: "backend",
        sessionId: response.session.session_id
      });
    } catch (caught) {
      setError(toDisplayError(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleFinalize() {
    if (!session || session.answers.length === 0) {
      return;
    }

    setError(null);
    setIsFinalizing(true);
    try {
      const response = await finalizeAssessment(session.session_id);
      setSession(response.session);
      setResult(response.result);
      setCurrentQuestion(null);
      updateDashboardRunState({
        dataMode: "backend",
        sessionId: response.session.session_id
      });
    } catch (caught) {
      setError(toDisplayError(caught));
    } finally {
      setIsFinalizing(false);
    }
  }

  return (
    <div className={styles.workspace}>
      <section className={styles.heroPanel} aria-labelledby="assessment-title">
        <div className={styles.heroCopy}>
          <p className={styles.eyebrow}>Goal intake and diagnostic assessment</p>
          <h2 className={styles.heroTitle} id="assessment-title">
            Build the learner profile before generating the path.
          </h2>
          <p className={styles.heroText}>
            UI-2 stops at the finalized knowledge map. Curriculum, resources, quiz,
            progress, and adaptation remain in later product screens.
          </p>
          <div className={styles.chipRow}>
            <StatusBadge tone="info">Local no-auth</StatusBadge>
            <StatusBadge tone="warning">In-memory session</StatusBadge>
            <StatusBadge tone="neutral">Mock-safe</StatusBadge>
          </div>
        </div>
        <div className={styles.diagnosticCard}>
          <div>
            <span>Current stage</span>
            <strong>{isCompleted ? "Knowledge map ready" : session ? "Assessment active" : "Goal intake"}</strong>
          </div>
          <div>
            <span>Evidence</span>
            <strong>{progress ? `${progress.answered_count} answers` : "Not started"}</strong>
          </div>
          <div>
            <span>Confidence</span>
            <strong>{progress ? `${Math.round(progress.confidence_score * 100)}%` : "0%"}</strong>
          </div>
        </div>
      </section>

      <WorkflowStepper
        description="UI-2 activates the first two workflow stages and leaves later stages visible for context."
        steps={workflowSteps}
        title="Assessment workflow"
        variant="compact"
      />

      {error ? <ErrorState message={error} title="Assessment request failed" /> : null}

      <section className={styles.grid}>
        <div className={styles.stack}>
          <GoalIntakeForm
            disabled={Boolean(session) && !isCompleted}
            isLoading={isStarting}
            onChange={setFormValue}
            onSubmit={handleStartAssessment}
            value={formValue}
          />
          <AssessmentProgressPanel progress={progress} session={session} />
        </div>

        <div className={styles.stack}>
          <AssessmentQuestionCard
            answer={answer}
            disabled={!session || isCompleted}
            isSubmitting={isSubmitting}
            onAnswerChange={setAnswer}
            onSubmit={handleSubmitAnswer}
            question={currentQuestion}
          />
          <AnswerFeedbackPanel evaluation={evaluation} />
          <FinalizeControls
            canFinalize={Boolean(session && session.answers.length > 0 && !isCompleted)}
            isFinalizing={isFinalizing}
            onFinalize={handleFinalize}
          />
          <KnowledgeMapPreview knowledgeMap={knowledgeMap} progress={progress} />
        </div>
      </section>
    </div>
  );
}

function FinalizeControls({
  canFinalize,
  isFinalizing,
  onFinalize
}: {
  canFinalize: boolean;
  isFinalizing: boolean;
  onFinalize: () => void;
}) {
  return (
    <div className={styles.buttonRow}>
      <Button
        disabled={!canFinalize || isFinalizing}
        isLoading={isFinalizing}
        onClick={onFinalize}
        type="button"
        variant="secondary"
      >
        Finalize Knowledge Map
      </Button>
      <span className={styles.hint}>
        Manual finalization is available after at least one answer.
      </span>
    </div>
  );
}

function buildAssessmentSteps(
  session: AssessmentSession | null,
  result: FinalAssessmentResult | null,
  error: string | null
): WorkflowStep[] {
  return pathaiWorkflowSteps.map((step) => {
    if (step.id === "assessment") {
      if (error) {
        return { ...step, status: "failed" };
      }
      if (result) {
        return { ...step, status: "done" };
      }
      if (session) {
        return { ...step, status: "running" };
      }
      return { ...step, status: "pending" };
    }

    if (step.id === "knowledge-map") {
      if (result) {
        return { ...step, status: "done" };
      }
      if (session) {
        return { ...step, status: "running" };
      }
      return { ...step, status: "pending" };
    }

    return { ...step, status: result ? "blocked" : "pending" };
  });
}

function toDisplayError(error: unknown): string {
  if (error instanceof PathAIFrontendApiError) {
    return `${error.message}${error.code ? ` (${error.code})` : ""}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "The assessment request failed.";
}
