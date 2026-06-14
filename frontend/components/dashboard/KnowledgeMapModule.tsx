import { classNames } from "@/components/ui/classNames";
import type { KnowledgeItem } from "@/lib/dashboard/types";

import styles from "./CommandCenterDashboard.module.css";

type KnowledgeMapModuleProps = {
  items: KnowledgeItem[];
};

export function KnowledgeMapModule({ items }: KnowledgeMapModuleProps) {
  const strong = items.filter((item) => item.tone === "strong");
  const gaps = items.filter((item) => item.tone === "gap");

  return (
    <section className={styles.module} aria-labelledby="knowledge-map-title">
      <header className={styles.cardHeader}>
        <h2 className={styles.cardTitle} id="knowledge-map-title">
          <span aria-hidden="true">Map</span>
          Architectural Mastery
        </h2>
        <span className={styles.metaPill}>Explore map</span>
      </header>
      <div className={styles.moduleBody}>
        <div className={styles.knowledgeGrid}>
          <KnowledgeColumn title="Strong concepts" items={strong} />
          <div className={styles.knowledgeColumn}>
            <KnowledgeColumn title="Critical gaps" items={gaps} />
            <p className={styles.knowledgeNote}>Connected to Week 2 adaptation protocol.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function KnowledgeColumn({ items, title }: { items: KnowledgeItem[]; title: string }) {
  return (
    <div className={styles.knowledgeColumn}>
      <h3 className={styles.columnTitle}>{title}</h3>
      <div className={styles.conceptList}>
        {items.map((item) => (
          <span
            className={classNames(
              styles.conceptChip,
              item.tone === "gap" && styles.conceptGap
            )}
            key={item.label}
          >
            {item.label}
            <span className={styles.conceptScore}>{item.score.toFixed(2)}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
