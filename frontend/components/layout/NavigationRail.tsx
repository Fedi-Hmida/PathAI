import Link from "next/link";

import { StatusBadge } from "@/components/ui";

import styles from "./NavigationRail.module.css";

export type NavigationItemId =
  | "command-center"
  | "demo"
  | "assessment"
  | "knowledge-map"
  | "curriculum"
  | "resources"
  | "critic"
  | "quiz"
  | "progress"
  | "adaptation"
  | "agents"
  | "evaluation";

type NavigationItem = {
  disabled?: boolean;
  href: string;
  id: NavigationItemId;
  label: string;
  meta?: string;
};

const navigationItems: NavigationItem[] = [
  { href: "/command-center", id: "command-center", label: "Command Center", meta: "visual" },
  { href: "/demo", id: "demo", label: "Demo", meta: "live" },
  { href: "/learn/new", id: "assessment", label: "Goal / Assessment", meta: "live" },
  { disabled: true, href: "/learn/demo/map", id: "knowledge-map", label: "Knowledge Map" },
  { href: "/dashboard/demo", id: "curriculum", label: "Curriculum", meta: "preview" },
  { disabled: true, href: "/learn/demo/resources", id: "resources", label: "Resources" },
  { disabled: true, href: "/learn/demo/review", id: "critic", label: "Critic" },
  { disabled: true, href: "/learn/demo/quiz/demo", id: "quiz", label: "Quiz" },
  { disabled: true, href: "/learn/demo/progress", id: "progress", label: "Progress" },
  { disabled: true, href: "/learn/demo/adaptation", id: "adaptation", label: "Adaptation" },
  { disabled: true, href: "/learn/demo/agents", id: "agents", label: "Agents" },
  { disabled: true, href: "/learn/demo/evaluation", id: "evaluation", label: "Evaluation" }
];

type NavigationRailProps = {
  activeItem: NavigationItemId;
};

export function NavigationRail({ activeItem }: NavigationRailProps) {
  return (
    <aside aria-label="PathAI workflow navigation" className={styles.rail}>
      <div className={styles.summary}>
        <StatusBadge tone="info">Local no-auth</StatusBadge>
        <div>
          <p className={styles.summaryTitle}>Workflow surface</p>
          <p className={styles.summaryText}>
            Demo is live. Later workflow pages are marked until their UI phases are built.
          </p>
        </div>
      </div>
      <ol className={styles.list}>
        {navigationItems.map((item, index) => (
          <li className={styles.item} key={item.id}>
            {item.disabled ? (
              <span
                aria-disabled="true"
                className={styles.disabled}
                title={`${item.label} is planned for a later UI phase`}
              >
                <span className={styles.index}>{index + 1}</span>
                <span className={styles.label}>{item.label}</span>
                <span className={styles.meta}>soon</span>
              </span>
            ) : (
              <Link
                aria-current={activeItem === item.id ? "page" : undefined}
                className={`${styles.link} ${activeItem === item.id ? styles.active : ""}`}
                href={item.href}
              >
                <span className={styles.index}>{index + 1}</span>
                <span className={styles.label}>{item.label}</span>
                {item.meta ? <span className={styles.meta}>{item.meta}</span> : null}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </aside>
  );
}
