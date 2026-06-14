import type {
  AgentStep,
  CommandCenterDashboardData,
  CriticIssue,
  CurriculumWeek,
  KnowledgeItem,
  PipelineStatusItem,
  QuickResource,
  QuizOption,
  ResourceCard,
  SystemHealthMetric,
  SystemMetric
} from "@/lib/dashboard/types";

export const commandCenterMock = {
  learner: {
    goal: "Architecting RAG Systems for Graduation",
    subtitle:
      "Designing high-performance retrieval-augmented pipelines with FAISS and multi-modal embeddings.",
    level: "Intermediate",
    weekLabel: "Week 2 of 4",
    mastery: 37,
    runtime: "Active",
    build: "PathAI v4 pro"
  },
  agentSteps: [
    {
      detail: "Identified 3 conceptual gaps in vector search fundamentals.",
      label: "Assessor",
      model: "Mock LLM",
      status: "success"
    },
    {
      detail: "Synthesizing adaptive module for chunking strategies.",
      label: "Curriculum",
      model: "Planner",
      status: "running"
    },
    {
      detail: "Waiting for curriculum schema before refreshing matches.",
      label: "Resource",
      model: "RAG",
      status: "idle"
    },
    {
      detail: "Validation queue prepared for coherence and coverage checks.",
      label: "Critic",
      model: "Quality",
      status: "warning"
    }
  ] satisfies AgentStep[],
  pipelineStatus: [
    { label: "Assessment", state: "Knowledge map ready", tone: "success" },
    { label: "Curriculum", state: "Week 2 active", tone: "running" },
    { label: "Resources", state: "Coverage warning", tone: "warning" },
    { label: "Critic", state: "Revision requested", tone: "warning" },
    { label: "Adapter", state: "Replan prepared", tone: "running" }
  ] satisfies PipelineStatusItem[],
  nextAction: {
    action: "Take the chunking checkpoint",
    detail:
      "Complete the focused knowledge check before moving to vector databases. The adapter flagged chunking as the active blocker.",
    due: "Estimated 12 minutes",
    reason: "Low quiz confidence and one stuck topic in Week 2"
  },
  learningPathProgress: {
    completedWeeks: 1,
    currentFocus: "Chunking and semantic retrieval",
    pace: "Behind schedule by 1 focused session",
    progress: 37,
    totalWeeks: 4
  },
  curriculumWeeks: [
    {
      detail: "NumPy, PyTorch basics, transformer architecture",
      focus: "Foundations",
      label: "Mastered",
      status: "completed",
      week: 1
    },
    {
      detail: "Chunking strategies with a detected difficulty spike",
      focus: "Embeddings",
      label: "Current week",
      status: "current",
      week: 2
    },
    {
      detail: "FAISS, Pinecone, HNSW indexing, retrieval latency",
      focus: "Vector Databases",
      label: "Locked",
      status: "locked",
      week: 3
    },
    {
      detail: "End-to-end orchestration and graduation MVP integration",
      focus: "MVP Integration",
      label: "Milestone",
      status: "milestone",
      week: 4
    }
  ] satisfies CurriculumWeek[],
  knowledge: [
    { label: "Python Core", score: 0.94, tone: "strong" },
    { label: "Transformer Architecture", score: 0.91, tone: "strong" },
    { label: "PyTorch", score: 0.88, tone: "strong" },
    { label: "Chunking Logic", score: 0.42, tone: "gap" },
    { label: "Vector Search", score: 0.31, tone: "gap" }
  ] satisfies KnowledgeItem[],
  quiz: {
    eyebrow: "Unit 2.4: Context Windows",
    question: "What is the primary constraint when choosing a chunking strategy for long-context RAG?",
    options: [
      { label: "A", text: "Total corpus embedding cost reduction" },
      {
        correct: true,
        label: "B",
        text: "Maximizing contextual relevance within model window"
      },
      { label: "C", text: "Reducing latency of similarity calculations" }
    ] satisfies QuizOption[]
  },
  resources: [
    {
      difficulty: "Advanced",
      kind: "Paper",
      rating: "4.9 / 5.0",
      source: "SBERT.net",
      summary: "Explains the theoretical basis for bi-encoder architectures used in modern RAG.",
      title: "Sentence-BERT Deep Dive",
      tone: "indigo"
    },
    {
      difficulty: "Technical",
      kind: "Docs",
      rating: "4.8 / 5.0",
      source: "Meta AI",
      summary: "How to choose between Flat, IVF, and HNSW for varying corpus sizes.",
      title: "FAISS Indexing Strategies",
      tone: "teal"
    },
    {
      difficulty: "Practical",
      kind: "Recipe",
      rating: "5.0 / 5.0",
      source: "LangChain",
      summary: "Implementation scripts for semantic-aware text splitting.",
      title: "Adaptive Chunking Cookbook",
      tone: "amber"
    }
  ] satisfies ResourceCard[],
  critic: {
    decision: "Needs revision",
    score: 0.76,
    issues: [
      {
        detail: "Week 2 heavily favors academic papers over implementation labs.",
        solution: "Add one implementation lab and one short applied tutorial before the FAISS module.",
        title: "Resource imbalance"
      },
      {
        detail: "Transition from Week 1 transformers to Week 2 FAISS is too abrupt.",
        solution: "Insert a compact bridge lesson on embedding spaces and nearest-neighbor search.",
        title: "Coherence gap"
      }
    ] satisfies CriticIssue[]
  },
  adaptation: {
    after: "Reinforced",
    before: "Standard",
    message:
      "Based on the recent chunking quiz score, PathAI prepared a reinforced lab for chunking and vector logic.",
    trigger: "Replan triggered"
  },
  metrics: [
    { label: "Coherence Score", value: "0.92" },
    { label: "Information Entropy", value: "0.14" },
    { label: "Faithfulness", value: "0.98" }
  ] satisfies SystemMetric[],
  systemHealth: [
    {
      detail: "Moderate",
      label: "Cognitive load",
      tone: "warning",
      value: "68%"
    },
    {
      detail: "Stable",
      label: "Retention rate",
      tone: "success",
      value: "81%"
    },
    {
      detail: "Demo runtime",
      label: "Tokens processed",
      tone: "info",
      value: "42.8k"
    },
    {
      detail: "Assessor, planner, critic",
      label: "Active agents",
      tone: "success",
      value: "3"
    }
  ] satisfies SystemHealthMetric[],
  quickResources: [
    {
      action: "Open",
      label: "Chunking lab",
      meta: "Practical - 18 min"
    },
    {
      action: "Review",
      label: "FAISS primer",
      meta: "Docs - 22 min"
    },
    {
      action: "Compare",
      label: "RAG eval checklist",
      meta: "Rubric - 10 min"
    }
  ] satisfies QuickResource[],
  runtimeLogs: ["init_agent_orchestrator", "hook_critic_evaluation", "adaptive_path_gen_02.json"],
  runtimeStatus: {
    backend: "checking",
    dataMode: "mock",
    errors: [],
    llmMode: "mock-safe",
    message: "Sample preview data. Start an assessment or run the backend demo to select a local run.",
    readiness: "checking"
  }
} satisfies CommandCenterDashboardData;
