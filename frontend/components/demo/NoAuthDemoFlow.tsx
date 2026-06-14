"use client";

import { useState, type ReactNode } from "react";

import styles from "./NoAuthDemoFlow.module.css";
import type { CurriculumPlan, KnowledgeMap } from "@/lib/api/curriculum";
import {
  attachResources,
  checkAdaptation,
  finalizeAssessment,
  generateCurriculumFromAssessment,
  generateQuiz,
  getQuizHistory,
  initializeProgress,
  PathAIDemoApiError,
  reviewCurriculum,
  runAdaptationReplan,
  runEvaluationSample,
  runServiceBackedDemo,
  startAssessment,
  submitAssessmentAnswer,
  submitQuiz,
  updateProgress,
  type AdaptationDecision,
  type AdaptationResult,
  type AssessmentQuestion,
  type AssessmentSession,
  type CriticReviewResult,
  type DemoGoalInput,
  type EvaluationReport,
  type ProgressSummary,
  type Quiz,
  type QuizHistory,
  type QuizResult,
  type ResourceAttachmentResponse,
  type ServiceBackedDemoResult
} from "@/lib/api/demo";
import { updateDashboardRunState } from "@/lib/dashboard/runState";

type StepState = "pending" | "running" | "done" | "failed";

type DemoStep = {
  id: string;
  label: string;
  status: StepState;
  detail?: string;
};

const initialInput: DemoGoalInput = {
  goal: "Learn RAG systems for a graduation project",
  timeline_weeks: 4,
  hours_per_week: 6,
  target_level: "beginner",
  max_questions: 3
};

const initialSteps: DemoStep[] = [
  { id: "start", label: "Start assessment", status: "pending" },
  { id: "answer", label: "Submit assessment answer", status: "pending" },
  { id: "map", label: "Finalize knowledge map", status: "pending" },
  { id: "curriculum", label: "Generate curriculum", status: "pending" },
  { id: "resources", label: "Attach resources", status: "pending" },
  { id: "critic", label: "Run critic review", status: "pending" },
  { id: "progress", label: "Initialize and update progress", status: "pending" },
  { id: "quiz", label: "Generate and submit quiz", status: "pending" },
  { id: "adapter", label: "Check and run adaptation", status: "pending" },
  { id: "evaluation", label: "Run synthetic evaluation", status: "pending" },
  { id: "orchestration", label: "Verify service-backed orchestration", status: "pending" }
];

type NoAuthDemoFlowProps = {
  embedded?: boolean;
};

export function NoAuthDemoFlow({ embedded = false }: NoAuthDemoFlowProps) {
  const [input, setInput] = useState<DemoGoalInput>(initialInput);
  const [answer, setAnswer] = useState(
    "Embeddings represent text as vectors so a retriever can find semantically similar chunks."
  );
  const [steps, setSteps] = useState<DemoStep[]>(initialSteps);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [session, setSession] = useState<AssessmentSession | null>(null);
  const [question, setQuestion] = useState<AssessmentQuestion | null>(null);
  const [knowledgeMap, setKnowledgeMap] = useState<KnowledgeMap | null>(null);
  const [curriculum, setCurriculum] = useState<CurriculumPlan | null>(null);
  const [resources, setResources] = useState<ResourceAttachmentResponse | null>(null);
  const [critic, setCritic] = useState<CriticReviewResult | null>(null);
  const [progress, setProgress] = useState<ProgressSummary | null>(null);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);
  const [quizHistory, setQuizHistory] = useState<QuizHistory | null>(null);
  const [adaptationDecision, setAdaptationDecision] = useState<AdaptationDecision | null>(null);
  const [adaptation, setAdaptation] = useState<AdaptationResult | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationReport | null>(null);
  const [serviceBackedRun, setServiceBackedRun] = useState<ServiceBackedDemoResult | null>(null);

  function markStep(id: string, status: StepState, detail?: string) {
    setSteps((current) =>
      current.map((step) => (step.id === id ? { ...step, status, detail } : step))
    );
  }

  function handleFailure(stepId: string, caught: unknown) {
    const message =
      caught instanceof PathAIDemoApiError || caught instanceof Error
        ? caught.message
        : "The demo flow failed.";
    markStep(stepId, "failed", message);
    setError(message);
  }

  function resetOutputs() {
    setSteps(initialSteps);
    setSession(null);
    setQuestion(null);
    setKnowledgeMap(null);
    setCurriculum(null);
    setResources(null);
    setCritic(null);
    setProgress(null);
    setQuiz(null);
    setQuizResult(null);
    setQuizHistory(null);
    setAdaptationDecision(null);
    setAdaptation(null);
    setEvaluation(null);
    setServiceBackedRun(null);
  }

  async function handleStartAssessment() {
    resetOutputs();
    setIsRunning(true);
    setError(null);
    try {
      markStep("start", "running");
      const started = await startAssessment(input);
      setSession(started.session);
      setQuestion(started.next_question);
      updateDashboardRunState({
        dataMode: "backend",
        sessionId: started.session.session_id
      });
      markStep("start", "done", started.next_question.topic);
    } catch (caught) {
      handleFailure("start", caught);
    } finally {
      setIsRunning(false);
    }
  }

  async function handleRunRemainingFlow() {
    if (!session) {
      setError("Start the assessment first.");
      return;
    }
    setIsRunning(true);
    setError(null);
    let activeStep = "answer";
    try {
      markStep("answer", "running");
      await submitAssessmentAnswer(session.session_id, answer);
      markStep("answer", "done", "Answer accepted by the assessment service.");

      activeStep = "map";
      markStep("map", "running");
      const finalized = await finalizeAssessment(session.session_id);
      setKnowledgeMap(finalized.result.knowledge_map);
      markStep("map", "done", `Confidence ${finalized.result.knowledge_map.confidence_score.toFixed(2)}`);

      activeStep = "curriculum";
      markStep("curriculum", "running");
      const generatedCurriculum = await generateCurriculumFromAssessment(session.session_id);
      setCurriculum(generatedCurriculum);
      updateDashboardRunState({
        curriculumId: generatedCurriculum.curriculum_id,
        dataMode: "backend",
        sessionId: session.session_id
      });
      markStep("curriculum", "done", `${generatedCurriculum.weeks.length} weeks generated`);

      activeStep = "resources";
      markStep("resources", "running");
      const attachedResources = await attachResources(generatedCurriculum);
      setResources(attachedResources);
      markStep("resources", "done", `${attachedResources.attachments.length} topics enriched`);

      activeStep = "critic";
      markStep("critic", "running");
      const criticReview = await reviewCurriculum(generatedCurriculum, attachedResources);
      setCritic(criticReview);
      markStep("critic", "done", `${criticReview.decision} (${criticReview.overall_quality_score.toFixed(2)})`);

      activeStep = "progress";
      markStep("progress", "running");
      const initializedProgress = await initializeProgress(generatedCurriculum);
      const updatedProgress = await updateProgress(initializedProgress.summary, "stuck");
      setProgress(updatedProgress.summary);
      markStep("progress", "done", "First topic marked stuck to trigger adaptation");

      activeStep = "quiz";
      markStep("quiz", "running");
      const generatedQuiz = await generateQuiz(generatedCurriculum, attachedResources);
      setQuiz(generatedQuiz.quiz);
      updateDashboardRunState({
        curriculumId: generatedCurriculum.curriculum_id,
        dataMode: "backend",
        quizId: generatedQuiz.quiz.quiz_id,
        sessionId: session.session_id
      });
      const scoredQuiz = await submitQuiz(generatedQuiz.quiz);
      setQuizResult(scoredQuiz);
      const history = await getQuizHistory(generatedCurriculum.curriculum_id);
      setQuizHistory(history);
      markStep("quiz", "done", `Score ${Math.round(scoredQuiz.score * 100)}%`);

      activeStep = "adapter";
      markStep("adapter", "running");
      const decision = await checkAdaptation(generatedCurriculum, updatedProgress.summary, history);
      setAdaptationDecision(decision);
      const replan = await runAdaptationReplan(
        generatedCurriculum,
        updatedProgress.summary,
        history,
        attachedResources
      );
      setAdaptation(replan);
      updateDashboardRunState({
        adaptationId: replan.adaptation_id,
        curriculumId: generatedCurriculum.curriculum_id,
        dataMode: "backend",
        quizId: generatedQuiz.quiz.quiz_id,
        sessionId: session.session_id
      });
      markStep("adapter", "done", replan.decision.decision);

      activeStep = "evaluation";
      markStep("evaluation", "running");
      const report = await runEvaluationSample();
      setEvaluation(report);
      markStep("evaluation", "done", `${report.metric_scores.length} synthetic metrics`);

      activeStep = "orchestration";
      markStep("orchestration", "running");
      const serviceRun = await runServiceBackedDemo(input);
      setServiceBackedRun(serviceRun);
      markStep("orchestration", "done", serviceRun.run_id);
    } catch (caught) {
      handleFailure(activeStep, caught);
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className={`${styles.demoPage} ${embedded ? styles.embedded : ""}`}>
      <section className={styles.intro}>
        <div>
          <p className={styles.eyebrow}>Local no-auth demo</p>
          <h1>PathAI working flow</h1>
          <p>
            Run the current backend pipeline without login: assessment, curriculum,
            resources, critic, progress, quiz, adaptation, and synthetic evaluation.
          </p>
        </div>
        <div className={styles.notice}>
          Mock-safe local mode. Runtime data is in-memory and resets when the backend restarts.
        </div>
      </section>

      <section className={styles.workspace}>
        <aside className={`${styles.panel} ${styles.controlPanel}`}>
          <h2>Goal Intake</h2>
          <label>
            Learning goal
            <textarea
              value={input.goal}
              onChange={(event) => setInput({ ...input, goal: event.target.value })}
              rows={4}
            />
          </label>
          <div className={styles.fieldGrid}>
            <label>
              Weeks
              <input
                type="number"
                min={1}
                max={12}
                value={input.timeline_weeks}
                onChange={(event) =>
                  setInput({ ...input, timeline_weeks: Number(event.target.value) })
                }
              />
            </label>
            <label>
              Hours/week
              <input
                type="number"
                min={1}
                max={40}
                value={input.hours_per_week}
                onChange={(event) =>
                  setInput({ ...input, hours_per_week: Number(event.target.value) })
                }
              />
            </label>
          </div>
          <label>
            Target level
            <select
              value={input.target_level}
              onChange={(event) =>
                setInput({ ...input, target_level: event.target.value as DemoGoalInput["target_level"] })
              }
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </label>

          <button type="button" onClick={handleStartAssessment} disabled={isRunning}>
            Start Assessment
          </button>

          {question ? (
            <div className={styles.questionBox}>
              <span>{question.topic}</span>
              <strong>{question.prompt}</strong>
              <label>
                Demo answer
                <textarea
                  rows={4}
                  value={answer}
                  onChange={(event) => setAnswer(event.target.value)}
                />
              </label>
              <button type="button" onClick={handleRunRemainingFlow} disabled={isRunning}>
                Run Remaining Demo Flow
              </button>
            </div>
          ) : null}

          {error ? <p className={styles.errorText}>{error}</p> : null}
        </aside>

        <section className={styles.panel}>
          <h2>Execution Steps</h2>
          <ol className={styles.stepList}>
            {steps.map((step) => (
              <li key={step.id} data-status={step.status}>
                <span>{step.label}</span>
                <strong>{step.status}</strong>
                {step.detail ? <small>{step.detail}</small> : null}
              </li>
            ))}
          </ol>
        </section>
      </section>

      <section className={styles.resultsGrid}>
        <ResultPanel title="Knowledge Map">
          {knowledgeMap ? <KnowledgeMapView map={knowledgeMap} /> : <EmptyState />}
        </ResultPanel>

        <ResultPanel title="Curriculum">
          {curriculum ? (
            <div className={styles.compactList}>
              {curriculum.weeks.map((week) => (
                <div key={week.week_number}>
                  <strong>Week {week.week_number}: {week.theme}</strong>
                  <span>{week.estimated_hours.toFixed(1)}h - {week.difficulty}</span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState />
          )}
        </ResultPanel>

        <ResultPanel title="Resources">
          {resources ? (
            <div className={styles.compactList}>
              {resources.attachments.slice(0, 4).map((attachment) => (
                <div key={attachment.topic_id}>
                  <strong>{attachment.topic}</strong>
                  <span>{attachment.resources[0]?.title ?? "No resource matched"}</span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState />
          )}
        </ResultPanel>

        <ResultPanel title="Critic Review">
          {critic ? (
            <div className={styles.metricBlock}>
              <strong>{critic.decision}</strong>
              <span>Quality score: {critic.overall_quality_score.toFixed(2)}</span>
              {critic.revision_instructions.slice(0, 2).map((item) => (
                <p key={`${item.target}-${item.instruction}`}>{item.instruction}</p>
              ))}
            </div>
          ) : (
            <EmptyState />
          )}
        </ResultPanel>

        <ResultPanel title="Progress & Quiz">
          {progress && quizResult ? (
            <div className={styles.metricBlock}>
              <strong>{progress.analytics.completion_percentage.toFixed(1)}% complete</strong>
              <span>Stuck topics: {progress.analytics.stuck_topic_count}</span>
              <span>Quiz score: {Math.round(quizResult.score * 100)}%</span>
              {quizHistory ? <span>Quiz attempts: {quizHistory.attempts.length}</span> : null}
              {quiz ? <span>Quiz questions: {quiz.questions.length}</span> : null}
            </div>
          ) : (
            <EmptyState />
          )}
        </ResultPanel>

        <ResultPanel title="Adapter">
          {adaptation && adaptationDecision ? (
            <div className={styles.metricBlock}>
              <strong>{adaptation.decision.decision}</strong>
              <span>{adaptationDecision.trigger_reason}</span>
              <p>{adaptation.notification?.message ?? adaptationDecision.trigger_details}</p>
            </div>
          ) : (
            <EmptyState />
          )}
        </ResultPanel>

        <ResultPanel title="Evaluation">
          {evaluation ? (
            <div className={styles.metricBlock}>
              <strong>{evaluation.system_variant}</strong>
              <span>{evaluation.metric_scores.length} synthetic metrics</span>
              <p>{evaluation.limitations[0]}</p>
            </div>
          ) : (
            <EmptyState />
          )}
        </ResultPanel>

        <ResultPanel title="Service-Backed Orchestration">
          {serviceBackedRun ? (
            <div className={styles.metricBlock}>
              <strong>{serviceBackedRun.run_id}</strong>
              <span>{serviceBackedRun.steps.length} real-service steps completed</span>
              <span>Adapter: {serviceBackedRun.adaptation_result.decision.decision}</span>
            </div>
          ) : (
            <EmptyState />
          )}
        </ResultPanel>
      </section>

    </main>
  );

}

function ResultPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className={styles.resultPanel}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function EmptyState() {
  return <span className={styles.empty}>Waiting for this step.</span>;
}

function KnowledgeMapView({ map }: { map: KnowledgeMap }) {
  return (
    <div className={styles.compactList}>
      <TagGroup label="Strong" items={map.strong} />
      <TagGroup label="Weak" items={map.weak} />
      <TagGroup label="Missing" items={map.missing} />
      <span>Recommended level: {map.recommended_level}</span>
    </div>
  );
}

function TagGroup({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <strong>{label}</strong>
      <div className={styles.tagRow}>
        {items.length > 0 ? (
          items.map((item) => (
            <span className={styles.tag} key={`${label}-${item}`}>
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
