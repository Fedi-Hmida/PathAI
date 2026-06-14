"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getAdaptationHistory, type AdaptationHistoryResponse } from "@/lib/api/adapt";
import { getAssessmentSession, type AssessmentSessionResponse } from "@/lib/api/assessment";
import { PathAIFrontendApiError } from "@/lib/api/client";
import { getCurriculum, type CurriculumPlan } from "@/lib/api/curriculum";
import { getEvaluationDatasets, getEvaluationRubrics } from "@/lib/api/evaluation";
import { getProgressSummary, type CurriculumProgressSummary } from "@/lib/api/progress";
import { getQuizHistory, type QuizHistorySummary } from "@/lib/api/quiz";
import { getHealth, getReadiness, getSafeLlmConfig } from "@/lib/api/runtime";
import { mergeCommandCenterData } from "@/lib/dashboard/adapters";
import {
  getDashboardRunState,
  isDashboardRunStateExpired,
  updateDashboardRunState,
  type DashboardRunState
} from "@/lib/dashboard/runState";
import type { CommandCenterDashboardData } from "@/lib/dashboard/types";
import { commandCenterMock } from "@/lib/demo/commandCenterMock";

import { AgentPipeline } from "./AgentPipeline";
import styles from "./CommandCenterDashboard.module.css";
import { CommandCenterHero } from "./CommandCenterHero";
import { CommandCenterSummaryCards } from "./CommandCenterSummaryCards";
import { CurriculumPathTimeline } from "./CurriculumPathTimeline";
import { DashboardRightInspector } from "./DashboardRightInspector";
import { KnowledgeCheckCard } from "./KnowledgeCheckCard";
import { KnowledgeMapModule } from "./KnowledgeMapModule";
import { PipelineStatusStrip } from "./PipelineStatusStrip";
import { RecommendedResources } from "./RecommendedResources";

const railLinks = [
  { href: "/command-center", label: "Command Center", meta: "Active", short: "CC" },
  { href: "/learn/new", label: "Goal Assessment", meta: "Live", short: "AS" },
  { href: "/demo", label: "Backend Flow", meta: "Live", short: "DE" },
  { href: "/dashboard/demo", label: "Curriculum Preview", meta: "Preview", short: "CU" },
  { href: "/", label: "Launch Home", meta: "Redirect", short: "HO" }
];

export function CommandCenterDashboard() {
  const [data, setData] = useState<CommandCenterDashboardData>(commandCenterMock);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function hydrateDashboard() {
      setIsRefreshing(true);

      const initialRunState = getDashboardRunState();
      const errors: string[] = [];
      let runState = initialRunState;

      if (isDashboardRunStateExpired(initialRunState)) {
        runState = updateDashboardRunState({ dataMode: "offline" });
        errors.push("Local dashboard run state is expired. Showing safe fallback data.");
      }

      const [health, readiness, llmConfig, datasets, rubrics] = await Promise.all([
        safeRead("health", getHealth()),
        safeRead("readiness", getReadiness()),
        safeRead("llm config", getSafeLlmConfig()),
        safeRead("evaluation datasets", getEvaluationDatasets()),
        safeRead("evaluation rubrics", getEvaluationRubrics())
      ]);

      errors.push(...compactErrors([health, readiness, llmConfig, datasets, rubrics]));

      const shouldFetchRun = Boolean(health.data && !isDashboardRunStateExpired(runState));
      let session: SafeRead<AssessmentSessionResponse> = emptyRead();
      let curriculum: SafeRead<CurriculumPlan> = emptyRead();
      let progress: SafeRead<CurriculumProgressSummary> = emptyRead();
      let quizHistory: SafeRead<QuizHistorySummary> = emptyRead();
      let adaptationHistory: SafeRead<AdaptationHistoryResponse> = emptyRead();

      if (shouldFetchRun) {
        [session, curriculum, progress, quizHistory, adaptationHistory] = await Promise.all([
          runState.sessionId
            ? safeRead("assessment session", getAssessmentSession(runState.sessionId))
            : emptyRead<AssessmentSessionResponse>(),
          runState.curriculumId
            ? safeRead("curriculum", getCurriculum(runState.curriculumId))
            : emptyRead<CurriculumPlan>(),
          runState.curriculumId
            ? safeRead("progress summary", getProgressSummary(runState.curriculumId))
            : emptyRead<CurriculumProgressSummary>(),
          runState.curriculumId
            ? safeRead("quiz history", getQuizHistory(runState.curriculumId))
            : emptyRead<QuizHistorySummary>(),
          runState.curriculumId
            ? safeRead("adaptation history", getAdaptationHistory(runState.curriculumId))
            : emptyRead<AdaptationHistoryResponse>()
        ]);
      }

      const runReads = [session, curriculum, progress, quizHistory, adaptationHistory];
      errors.push(...compactErrors(runReads));

      if (runReads.some((read) => read.status === 404)) {
        runState = updateDashboardRunState({ dataMode: "offline" });
        errors.push("Stored local run IDs were not found. The in-memory backend data may have expired.");
      } else if (health.data && (runState.sessionId || runState.curriculumId)) {
        runState = updateDashboardRunState({ dataMode: "backend" });
      } else if (!health.data && (runState.sessionId || runState.curriculumId)) {
        runState = updateDashboardRunState({ dataMode: "offline" });
      }

      const merged = mergeCommandCenterData({
        adaptationHistory: adaptationHistory.data,
        base: commandCenterMock,
        curriculum: curriculum.data,
        datasets: datasets.data,
        errors,
        health: health.data,
        llmConfig: llmConfig.data,
        progress: progress.data,
        quizHistory: quizHistory.data,
        readiness: readiness.data,
        runState,
        session: session.data?.session
      });

      if (!cancelled) {
        setData(merged);
        setIsRefreshing(false);
      }
    }

    void hydrateDashboard();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className={styles.dashboard}>
      <div className={styles.frame}>
        <aside className={styles.rail} aria-label="Command center navigation">
          <Link className={styles.logo} href="/" aria-label="PathAI home">
            P
          </Link>
          <div className={styles.railBrand}>
            <strong>PathAI</strong>
            <span>Learning OS</span>
          </div>
          <nav className={styles.railNav}>
            {railLinks.map((link) => (
              <Link
                aria-label={link.label}
                className={`${styles.railLink} ${
                  link.href === "/command-center" ? styles.railLinkActive : ""
                }`}
                href={link.href}
                key={link.href}
                title={link.label}
              >
                <span className={styles.railShort}>{link.short}</span>
                <span className={styles.railLabel}>{link.label}</span>
                <span className={styles.railMeta}>{link.meta}</span>
              </Link>
            ))}
          </nav>
          <div className={styles.railSpacer} />
          <button className={styles.railButton} title="Help" type="button">
            ?
          </button>
          <div className={styles.avatar} aria-label="Local demo learner">
            LD
          </div>
        </aside>

        <main className={styles.canvas}>
          <header className={styles.topbar}>
            <div className={styles.topbarTitle}>
              <h1>Command Center</h1>
              <div className={styles.runtimeChips}>
                <span className={styles.runtimeChip}>
                  Backend: {formatConnection(data.runtimeStatus.backend)}
                </span>
                <span className={styles.buildChip}>{data.runtimeStatus.llmMode}</span>
                <span className={styles.modeChip}>Data: {formatMode(data.runtimeStatus.dataMode)}</span>
              </div>
            </div>
            <div className={styles.searchCluster}>
              <label className={styles.visuallyHidden} htmlFor="command-search">
                Search architecture knowledge
              </label>
              <input
                className={styles.searchBox}
                id="command-search"
                placeholder="Search architecture knowledge..."
                type="search"
              />
              <button className={styles.iconButton} type="button" aria-label="View notifications">
                !
              </button>
            </div>
          </header>

          <div className={styles.content}>
            <section className={styles.dataNotice} data-mode={data.runtimeStatus.dataMode}>
              <div>
                <strong>{isRefreshing ? "Checking local run" : formatMode(data.runtimeStatus.dataMode)}</strong>
                <span>{data.runtimeStatus.message}</span>
              </div>
              <span>{formatReadiness(data.runtimeStatus.readiness)}</span>
            </section>
            <CommandCenterHero
              goal={data.learner.goal}
              level={data.learner.level}
              mastery={data.learner.mastery}
              subtitle={data.learner.subtitle}
              weekLabel={data.learner.weekLabel}
            />
            <CommandCenterSummaryCards
              learningPath={data.learningPathProgress}
              nextAction={data.nextAction}
            />
            <PipelineStatusStrip items={data.pipelineStatus} />
            <AgentPipeline agents={data.agentSteps} />
            <CurriculumPathTimeline weeks={data.curriculumWeeks} />
            <div className={styles.contentGrid}>
              <KnowledgeMapModule items={data.knowledge} />
              <KnowledgeCheckCard
                eyebrow={data.quiz.eyebrow}
                options={data.quiz.options}
                question={data.quiz.question}
              />
            </div>
            <RecommendedResources resources={data.resources} />
            <footer className={styles.footer}>
              <span>PathAI high-performance node v4.0.1</span>
              <div className={styles.footerLinks}>
                <Link href="/demo">Backend demo</Link>
                <Link href="/learn/new">Assessment</Link>
                <Link href="/">Home</Link>
              </div>
            </footer>
          </div>
        </main>

        <DashboardRightInspector
          adaptation={data.adaptation}
          critic={data.critic}
          metrics={data.metrics}
          quickResources={data.quickResources}
          runtimeLogs={data.runtimeLogs}
          systemHealth={data.systemHealth}
        />
      </div>
      <button className={styles.assistantAction} type="button">
        Ask PathAI
      </button>
    </div>
  );
}

type SafeRead<T> = {
  data: T | null;
  error: string | null;
  status: number | null;
};

async function safeRead<T>(label: string, promise: Promise<T>): Promise<SafeRead<T>> {
  try {
    return { data: await promise, error: null, status: null };
  } catch (error) {
    const status = error instanceof PathAIFrontendApiError ? error.status : null;
    const message = error instanceof Error ? error.message : "Request failed";
    return { data: null, error: `${label}: ${message}`, status };
  }
}

function emptyRead<T>(): SafeRead<T> {
  return { data: null, error: null, status: null };
}

function compactErrors(reads: Array<SafeRead<unknown>>): string[] {
  return reads.flatMap((read) => (read.error ? [read.error] : []));
}

function formatConnection(value: CommandCenterDashboardData["runtimeStatus"]["backend"]): string {
  if (value === "online") {
    return "Online";
  }
  if (value === "checking") {
    return "Checking";
  }
  if (value === "unavailable") {
    return "Unavailable";
  }
  return "Offline";
}

function formatMode(value: DashboardRunState["dataMode"]): string {
  if (value === "backend") {
    return "Backend data";
  }
  if (value === "offline") {
    return "Offline fallback";
  }
  return "Sample preview";
}

function formatReadiness(value: CommandCenterDashboardData["runtimeStatus"]["readiness"]): string {
  if (value === "ready") {
    return "Ready";
  }
  if (value === "not_ready") {
    return "Not ready";
  }
  if (value === "checking") {
    return "Checking";
  }
  return "Readiness unavailable";
}
