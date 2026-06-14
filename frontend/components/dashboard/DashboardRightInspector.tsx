import type {
  CriticIssue,
  QuickResource,
  SystemHealthMetric,
  SystemMetric
} from "@/lib/dashboard/types";

import { AdaptationProtocolPanel } from "./AdaptationProtocolPanel";
import { CriticAnalysisPanel } from "./CriticAnalysisPanel";
import styles from "./CommandCenterDashboard.module.css";
import { QuickResourcesPanel } from "./QuickResourcesPanel";
import { SystemHealthPanel } from "./SystemHealthPanel";

type DashboardRightInspectorProps = {
  adaptation: {
    after: string;
    before: string;
    message: string;
    trigger: string;
  };
  critic: {
    decision: string;
    issues: CriticIssue[];
    score: number;
  };
  metrics: SystemMetric[];
  quickResources: QuickResource[];
  runtimeLogs: string[];
  systemHealth: SystemHealthMetric[];
};

export function DashboardRightInspector({
  adaptation,
  critic,
  metrics,
  quickResources,
  runtimeLogs,
  systemHealth
}: DashboardRightInspectorProps) {
  return (
    <aside className={styles.inspector} aria-label="Dashboard inspector">
      <SystemHealthPanel metrics={systemHealth} />
      <CriticAnalysisPanel {...critic} />
      <AdaptationProtocolPanel {...adaptation} />
      <QuickResourcesPanel resources={quickResources} />
      <section className={styles.inspectorSection} aria-labelledby="architecture-health-title">
        <h2 className={styles.inspectorTitle} id="architecture-health-title">
          Architecture Health
        </h2>
        <div className={styles.metricList}>
          {metrics.map((metric) => (
            <div className={styles.metricItem} key={metric.label}>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
            </div>
          ))}
        </div>
        <div className={styles.logs}>
          <span>Runtime logs</span>
          <code>
            {runtimeLogs.map((log) => (
              <span key={log}>&gt; {log}</span>
            ))}
          </code>
        </div>
      </section>
    </aside>
  );
}
