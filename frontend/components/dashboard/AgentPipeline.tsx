import { classNames } from "@/components/ui/classNames";
import type { AgentStep } from "@/lib/dashboard/types";

import styles from "./CommandCenterDashboard.module.css";

type AgentPipelineProps = {
  agents: AgentStep[];
};

const signalByStatus: Record<AgentStep["status"], string> = {
  idle: "Idle",
  running: "Run",
  success: "Done",
  warning: "Watch"
};

export function AgentPipeline({ agents }: AgentPipelineProps) {
  return (
    <section aria-labelledby="agent-pipeline-title">
      <h2 className={styles.sectionLabel} id="agent-pipeline-title">
        Agent orchestration pipeline
      </h2>
      <div className={styles.pipeline}>
        {agents.map((agent) => (
          <article
            className={classNames(
              styles.agentCard,
              agent.status === "idle" && styles.agentCardIdle
            )}
            key={agent.label}
          >
            <div className={styles.agentTop}>
              <span
                className={classNames(
                  styles.agentModel,
                  agent.status === "success" && styles.agentModelSuccess,
                  agent.status === "running" && styles.agentModelRunning
                )}
              >
                {agent.model}
              </span>
              <span
                className={classNames(
                  styles.agentSignal,
                  agent.status === "success" && styles.agentSignalSuccess,
                  agent.status === "running" && styles.agentSignalRunning
                )}
              >
                {signalByStatus[agent.status]}
              </span>
            </div>
            <h3>{agent.label}</h3>
            <p>{agent.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
