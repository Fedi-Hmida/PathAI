import type {
  AssessmentSession,
  KnowledgeMap as AssessmentKnowledgeMap
} from "@/lib/api/assessment";
import type { CurriculumPlan } from "@/lib/api/curriculum";
import type { AdaptationHistoryResponse } from "@/lib/api/adapt";
import type { EvaluationDatasetsResponse } from "@/lib/api/evaluation";
import type { CurriculumProgressSummary } from "@/lib/api/progress";
import type { QuizHistorySummary } from "@/lib/api/quiz";
import type { HealthResponse, ReadinessResponse, SafeLLMConfig } from "@/lib/api/types";

import type {
  AgentStep,
  CommandCenterDashboardData,
  CommandCenterLearner,
  CommandCenterRuntimeStatus,
  CurriculumWeek,
  KnowledgeItem,
  LearningPathProgress,
  PipelineStatusItem,
  SystemHealthMetric,
  SystemMetric
} from "./types";
import type { DashboardRunState } from "./runState";

type MergeCommandCenterDataInput = {
  adaptationHistory?: AdaptationHistoryResponse | null;
  base: CommandCenterDashboardData;
  curriculum?: CurriculumPlan | null;
  datasets?: EvaluationDatasetsResponse | null;
  errors?: string[];
  health?: HealthResponse | null;
  llmConfig?: SafeLLMConfig | null;
  progress?: CurriculumProgressSummary | null;
  quizHistory?: QuizHistorySummary | null;
  readiness?: ReadinessResponse | null;
  runState: DashboardRunState;
  session?: AssessmentSession | null;
};

export function mergeCommandCenterData({
  adaptationHistory,
  base,
  curriculum,
  datasets,
  errors = [],
  health,
  llmConfig,
  progress,
  quizHistory,
  readiness,
  runState,
  session
}: MergeCommandCenterDataInput): CommandCenterDashboardData {
  const runtimeStatus = toRuntimeStatusViewModel({
    errors,
    health,
    llmConfig,
    readiness,
    runState
  });

  return {
    ...base,
    adaptation: toAdaptationPanelViewModel(adaptationHistory, base),
    agentSteps: toAgentStepsViewModel({ base, curriculum, progress, runState, session }),
    curriculumWeeks: toCurriculumTimelineViewModel(curriculum, progress, base),
    knowledge: toKnowledgeMapViewModel(session?.knowledge_map ?? curriculum?.knowledge_map ?? null, base),
    learner: toLearnerViewModel({ base, curriculum, progress, runtimeStatus, session }),
    learningPathProgress: toProgressSummaryViewModel(progress, curriculum, base),
    metrics: toEvaluationMetricsViewModel(datasets, base),
    nextAction: toNextActionViewModel({ adaptationHistory, base, progress, quizHistory, runState }),
    pipelineStatus: toPipelineStatusViewModel({ base, curriculum, progress, runState, session }),
    quiz: toQuizPreviewViewModel(quizHistory, base),
    runtimeLogs: toRuntimeLogsViewModel({ base, curriculum, errors, runState, session }),
    runtimeStatus,
    systemHealth: toSystemHealthViewModel({ base, health, llmConfig, readiness, runState })
  };
}

export function toSystemHealthViewModel({
  base,
  health,
  llmConfig,
  readiness,
  runState
}: {
  base: CommandCenterDashboardData;
  health?: HealthResponse | null;
  llmConfig?: SafeLLMConfig | null;
  readiness?: ReadinessResponse | null;
  runState: DashboardRunState;
}): SystemHealthMetric[] {
  return [
    {
      detail: health ? `${health.service} ${health.version}` : "Backend not reached",
      label: "Backend",
      tone: health ? "success" : "warning",
      value: health?.status === "ok" ? "Online" : "Offline"
    },
    {
      detail: readiness?.checks?.mongodb ?? "Unavailable or not checked",
      label: "Readiness",
      tone: readiness?.status === "ready" ? "success" : "warning",
      value: readiness?.status === "ready" ? "Ready" : "Not ready"
    },
    {
      detail: llmConfig
        ? `${llmConfig.model} - prompts ${llmConfig.prompt_version}`
        : "Dev config unavailable",
      label: "LLM mode",
      tone: llmConfig?.mock_mode === false ? "info" : "success",
      value: llmConfig ? (llmConfig.mock_mode ? "Mock" : "Real") : "Unknown"
    },
    {
      detail: runState.lastUpdatedAt === new Date(0).toISOString()
        ? "No selected local run"
        : `Updated ${formatShortTime(runState.lastUpdatedAt)}`,
      label: "Data source",
      tone: runState.dataMode === "backend" ? "success" : "info",
      value: modeLabel(runState.dataMode)
    },
    ...base.systemHealth.slice(0, 1)
  ];
}

export function toLearnerViewModel({
  base,
  curriculum,
  progress,
  runtimeStatus,
  session
}: {
  base: CommandCenterDashboardData;
  curriculum?: CurriculumPlan | null;
  progress?: CurriculumProgressSummary | null;
  runtimeStatus: CommandCenterRuntimeStatus;
  session?: AssessmentSession | null;
}): CommandCenterLearner {
  const totalWeeks = curriculum?.timeline_weeks ?? session?.timeline_weeks ?? null;
  const currentWeek = progress?.current_week_number ?? (curriculum ? 1 : null);
  const goal = curriculum?.goal ?? session?.goal ?? base.learner.goal;
  const mastery = clampPercentage(progress?.analytics.completion_percentage ?? base.learner.mastery);

  return {
    ...base.learner,
    build: runtimeStatus.readiness === "ready" ? "Backend ready" : "Local demo",
    goal,
    level: capitalize(curriculum?.knowledge_map.recommended_level ?? session?.target_level ?? base.learner.level),
    mastery,
    runtime: runtimeStatus.backend === "online" ? modeLabel(runtimeStatus.dataMode) : "Offline",
    subtitle:
      curriculum?.generation_notes?.[0] ??
      session?.assessment_notes?.[0] ??
      runtimeStatus.message,
    weekLabel:
      currentWeek && totalWeeks ? `Week ${currentWeek} of ${totalWeeks}` : base.learner.weekLabel
  };
}

export function toKnowledgeMapViewModel(
  knowledgeMap: AssessmentKnowledgeMap | null,
  base: CommandCenterDashboardData
): KnowledgeItem[] {
  if (!knowledgeMap) {
    return base.knowledge;
  }

  const strong = knowledgeMap.strong.map((label) => ({
    label,
    score: 0.9,
    tone: "strong" as const
  }));
  const weak = knowledgeMap.weak.map((label) => ({
    label,
    score: 0.45,
    tone: "gap" as const
  }));
  const missing = knowledgeMap.missing.map((label) => ({
    label,
    score: 0.2,
    tone: "gap" as const
  }));

  return [...strong, ...weak, ...missing].slice(0, 8);
}

export function toCurriculumTimelineViewModel(
  curriculum: CurriculumPlan | null | undefined,
  progress: CurriculumProgressSummary | null | undefined,
  base: CommandCenterDashboardData
): CurriculumWeek[] {
  if (!curriculum) {
    return base.curriculumWeeks;
  }

  const currentWeek = progress?.current_week_number ?? 1;
  return curriculum.weeks.map((week) => ({
    detail: week.weekly_goal || week.topics.map((topic) => topic.title).join(", "),
    focus: week.theme,
    label: week.week_number < currentWeek
      ? "Completed"
      : week.week_number === currentWeek
        ? "Current week"
        : week.project_or_application
          ? "Milestone"
          : "Planned",
    status: week.week_number < currentWeek
      ? "completed"
      : week.week_number === currentWeek
        ? "current"
        : week.project_or_application
          ? "milestone"
          : "locked",
    week: week.week_number
  }));
}

export function toProgressSummaryViewModel(
  progress: CurriculumProgressSummary | null | undefined,
  curriculum: CurriculumPlan | null | undefined,
  base: CommandCenterDashboardData
): LearningPathProgress {
  if (!progress) {
    return base.learningPathProgress;
  }

  const completedWeeks = progress.weeks.filter((week) => week.completion_percentage >= 100).length;
  const currentWeek = progress.weeks.find((week) => week.week_number === progress.current_week_number);
  return {
    completedWeeks,
    currentFocus: currentWeek?.theme ?? curriculum?.weeks[0]?.theme ?? base.learningPathProgress.currentFocus,
    pace: progress.analytics.stuck_topic_count > 0
      ? `${progress.analytics.stuck_topic_count} stuck topic signal`
      : "On track in local run",
    progress: clampPercentage(progress.analytics.completion_percentage),
    totalWeeks: curriculum?.timeline_weeks ?? progress.weeks.length
  };
}

export function toQuizPreviewViewModel(
  quizHistory: QuizHistorySummary | null | undefined,
  base: CommandCenterDashboardData
): CommandCenterDashboardData["quiz"] {
  if (!quizHistory || quizHistory.attempts.length === 0) {
    return base.quiz;
  }

  const averageScore = Math.round((quizHistory.average_score ?? quizHistory.best_score ?? 0) * 100);
  return {
    eyebrow: `${quizHistory.attempts.length} attempt${quizHistory.attempts.length === 1 ? "" : "s"} recorded`,
    options: [
      { correct: averageScore >= 70, label: "A", text: `Average score ${averageScore}%` },
      { correct: averageScore < 70, label: "B", text: `${quizHistory.low_score_count} low-score signal(s)` },
      { label: "C", text: `Best score ${Math.round((quizHistory.best_score ?? 0) * 100)}%` }
    ],
    question: "Latest backend quiz history is available for this local curriculum run."
  };
}

export function toAdaptationPanelViewModel(
  history: AdaptationHistoryResponse | null | undefined,
  base: CommandCenterDashboardData
): CommandCenterDashboardData["adaptation"] {
  const latest = history?.adaptations?.[0];
  if (!latest?.decision) {
    return base.adaptation;
  }

  return {
    after: latest.decision.decision,
    before: latest.decision.should_replan ? "Previous path" : "Current path",
    message:
      latest.notification?.message ??
      latest.decision.trigger_details ??
      "Adaptation history was loaded for this local curriculum.",
    trigger: latest.decision.trigger_reason
  };
}

function toRuntimeStatusViewModel({
  errors,
  health,
  llmConfig,
  readiness,
  runState
}: {
  errors: string[];
  health?: HealthResponse | null;
  llmConfig?: SafeLLMConfig | null;
  readiness?: ReadinessResponse | null;
  runState: DashboardRunState;
}): CommandCenterRuntimeStatus {
  const backend = health ? "online" : "offline";
  const readinessStatus = readiness?.status ?? (health ? "not_ready" : "unavailable");
  const hasRun = Boolean(runState.sessionId || runState.curriculumId);
  const dataMode = backend === "offline" && hasRun ? "offline" : runState.dataMode;
  const message = errors.length > 0
    ? errors[0]
    : hasRun
      ? "Connected to safe read data for the selected local run where available."
      : "Sample preview data. Start an assessment or run the backend demo to select a local run.";

  return {
    backend,
    dataMode,
    errors,
    llmMode: llmConfig ? (llmConfig.mock_mode ? "Mock LLM" : "Real LLM") : "LLM config unavailable",
    message,
    readiness: readinessStatus
  };
}

function toAgentStepsViewModel({
  base,
  curriculum,
  progress,
  runState,
  session
}: {
  base: CommandCenterDashboardData;
  curriculum?: CurriculumPlan | null;
  progress?: CurriculumProgressSummary | null;
  runState: DashboardRunState;
  session?: AssessmentSession | null;
}): AgentStep[] {
  if (!session && !curriculum && !progress) {
    return base.agentSteps;
  }

  return [
    {
      detail: session
        ? `${session.progress.answered_count} answer(s), confidence ${Math.round(session.confidence_score * 100)}%.`
        : "No selected assessment session.",
      label: "Assessor",
      model: "Backend read",
      status: session ? "success" : "idle"
    },
    {
      detail: curriculum
        ? `${curriculum.weeks.length} week plan loaded from curriculum store.`
        : "Waiting for curriculum ID.",
      label: "Curriculum",
      model: "Planner",
      status: curriculum ? "success" : "idle"
    },
    {
      detail: progress
        ? `${progress.analytics.stuck_topic_count} stuck topic(s), ${progress.analytics.completed_topic_count}/${progress.analytics.total_topic_count} done.`
        : "Progress read data not available yet.",
      label: "Progress",
      model: "Tracker",
      status: progress ? (progress.analytics.stuck_topic_count > 0 ? "warning" : "success") : "idle"
    },
    {
      detail: runState.curriculumId
        ? "Safe history reads enabled; replan remains manual."
        : "No curriculum selected for adaptation history.",
      label: "Adapter",
      model: "Signals",
      status: runState.curriculumId ? "running" : "idle"
    }
  ];
}

function toPipelineStatusViewModel({
  base,
  curriculum,
  progress,
  runState,
  session
}: {
  base: CommandCenterDashboardData;
  curriculum?: CurriculumPlan | null;
  progress?: CurriculumProgressSummary | null;
  runState: DashboardRunState;
  session?: AssessmentSession | null;
}): PipelineStatusItem[] {
  if (!session && !curriculum && !progress && runState.dataMode === "mock") {
    return base.pipelineStatus;
  }

  return [
    {
      label: "Assessment",
      state: session ? session.status : "No selected run",
      tone: session ? "success" : "idle"
    },
    {
      label: "Curriculum",
      state: curriculum ? `${curriculum.weeks.length} weeks loaded` : "Not selected",
      tone: curriculum ? "success" : "idle"
    },
    {
      label: "Progress",
      state: progress ? `${Math.round(progress.analytics.completion_percentage)}% complete` : "No summary",
      tone: progress ? "running" : "idle"
    },
    {
      label: "Quiz",
      state: runState.quizId ? "Quiz selected" : "History only",
      tone: runState.quizId ? "success" : "idle"
    },
    {
      label: "Adapter",
      state: runState.adaptationId ? "Result selected" : "Manual trigger",
      tone: runState.adaptationId ? "running" : "idle"
    }
  ];
}

function toNextActionViewModel({
  adaptationHistory,
  base,
  progress,
  quizHistory,
  runState
}: {
  adaptationHistory?: AdaptationHistoryResponse | null;
  base: CommandCenterDashboardData;
  progress?: CurriculumProgressSummary | null;
  quizHistory?: QuizHistorySummary | null;
  runState: DashboardRunState;
}): CommandCenterDashboardData["nextAction"] {
  if (runState.dataMode === "offline") {
    return {
      action: "Refresh the local run",
      detail: "The stored IDs may point to in-memory backend data that expired after restart.",
      due: "Local action",
      reason: "PathAI keeps the dashboard usable with sample fallback until you select a fresh run."
    };
  }

  if (progress?.analytics.stuck_topic_count) {
    return {
      action: "Review stuck topic",
      detail: "Open the progress or quiz workflow before manually triggering adaptation.",
      due: "Next learner action",
      reason: `${progress.analytics.stuck_topic_count} stuck topic signal(s) from backend progress.`
    };
  }

  if ((quizHistory?.low_score_count ?? 0) > 0) {
    return {
      action: "Retake focused quiz",
      detail: "Quiz history shows low-score signals. The adapter should remain a manual action.",
      due: "Before replanning",
      reason: `${quizHistory?.low_score_count ?? 0} low-score attempt(s) found.`
    };
  }

  const latestAdaptation = adaptationHistory?.adaptations?.[0];
  if (latestAdaptation?.decision?.should_replan) {
    return {
      action: "Inspect adaptation result",
      detail: latestAdaptation.notification?.message ?? latestAdaptation.decision.trigger_details,
      due: "Review required",
      reason: latestAdaptation.decision.trigger_reason
    };
  }

  return base.nextAction;
}

function toEvaluationMetricsViewModel(
  datasets: EvaluationDatasetsResponse | null | undefined,
  base: CommandCenterDashboardData
): SystemMetric[] {
  if (!datasets) {
    return base.metrics;
  }

  return [
    { label: "Synthetic Datasets", value: String(datasets.datasets.length) },
    { label: "Evaluation Mode", value: "Offline" },
    { label: "Claims", value: "Synthetic only" }
  ];
}

function toRuntimeLogsViewModel({
  base,
  curriculum,
  errors,
  runState,
  session
}: {
  base: CommandCenterDashboardData;
  curriculum?: CurriculumPlan | null;
  errors: string[];
  runState: DashboardRunState;
  session?: AssessmentSession | null;
}): string[] {
  const logs = [
    `data_mode:${runState.dataMode}`,
    session ? `assessment:${session.session_id}` : "assessment:none",
    curriculum ? `curriculum:${curriculum.curriculum_id}` : "curriculum:none",
    ...errors.map((error) => `warning:${error}`)
  ];

  return logs.length > 0 ? logs.slice(0, 5) : base.runtimeLogs;
}

function clampPercentage(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function capitalize(value: string): string {
  if (!value) {
    return value;
  }
  return `${value.charAt(0).toUpperCase()}${value.slice(1)}`;
}

function formatShortTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "unknown";
  }
  return date.toLocaleString(undefined, {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short"
  });
}

function modeLabel(mode: DashboardRunState["dataMode"]): string {
  if (mode === "backend") {
    return "Backend data";
  }
  if (mode === "offline") {
    return "Offline fallback";
  }
  return "Sample preview";
}
