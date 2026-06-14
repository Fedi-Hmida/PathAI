export type AgentStatus = "success" | "running" | "idle" | "warning";
export type WeekStatus = "completed" | "current" | "locked" | "milestone";
export type KnowledgeTone = "strong" | "gap";
export type PipelineStatusTone = "success" | "running" | "warning" | "idle";
export type ResourceTone = "indigo" | "teal" | "amber";
export type SystemHealthTone = "success" | "warning" | "info";
export type DashboardDataMode = "mock" | "backend" | "offline";
export type DashboardConnectionState = "checking" | "online" | "offline" | "unavailable";
export type DashboardReadinessState = "checking" | "ready" | "not_ready" | "unavailable";

export type AgentStep = {
  detail: string;
  label: string;
  model: string;
  status: AgentStatus;
};

export type CurriculumWeek = {
  detail: string;
  focus: string;
  label: string;
  status: WeekStatus;
  week: number;
};

export type KnowledgeItem = {
  label: string;
  score: number;
  tone: KnowledgeTone;
};

export type QuizOption = {
  correct?: boolean;
  label: string;
  text: string;
};

export type CommandCenterQuiz = {
  eyebrow: string;
  options: QuizOption[];
  question: string;
};

export type ResourceCard = {
  difficulty: string;
  kind: string;
  rating: string;
  source: string;
  summary: string;
  title: string;
  tone: ResourceTone;
};

export type CriticIssue = {
  detail: string;
  solution: string;
  title: string;
};

export type CommandCenterCritic = {
  decision: string;
  issues: CriticIssue[];
  score: number;
};

export type SystemMetric = {
  label: string;
  value: string;
};

export type SystemHealthMetric = {
  detail: string;
  label: string;
  tone: SystemHealthTone;
  value: string;
};

export type QuickResource = {
  action: string;
  label: string;
  meta: string;
};

export type PipelineStatusItem = {
  label: string;
  state: string;
  tone: PipelineStatusTone;
};

export type CommandCenterLearner = {
  build: string;
  goal: string;
  level: string;
  mastery: number;
  runtime: string;
  subtitle: string;
  weekLabel: string;
};

export type NextActionSummary = {
  action: string;
  detail: string;
  due: string;
  reason: string;
};

export type LearningPathProgress = {
  completedWeeks: number;
  currentFocus: string;
  pace: string;
  progress: number;
  totalWeeks: number;
};

export type AdaptationSummary = {
  after: string;
  before: string;
  message: string;
  trigger: string;
};

export type CommandCenterRuntimeStatus = {
  backend: DashboardConnectionState;
  dataMode: DashboardDataMode;
  errors: string[];
  llmMode: string;
  message: string;
  readiness: DashboardReadinessState;
};

export type CommandCenterDashboardData = {
  adaptation: AdaptationSummary;
  agentSteps: AgentStep[];
  critic: CommandCenterCritic;
  curriculumWeeks: CurriculumWeek[];
  knowledge: KnowledgeItem[];
  learner: CommandCenterLearner;
  learningPathProgress: LearningPathProgress;
  metrics: SystemMetric[];
  nextAction: NextActionSummary;
  pipelineStatus: PipelineStatusItem[];
  quickResources: QuickResource[];
  quiz: CommandCenterQuiz;
  resources: ResourceCard[];
  runtimeLogs: string[];
  runtimeStatus: CommandCenterRuntimeStatus;
  systemHealth: SystemHealthMetric[];
};
