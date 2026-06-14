import { Panel, StatusBadge } from "@/components/ui";
import type { AssessmentProgress, KnowledgeMap } from "@/lib/api/assessment";

import styles from "./Assessment.module.css";

type KnowledgeMapPreviewProps = {
  knowledgeMap: KnowledgeMap | null;
  progress?: AssessmentProgress | null;
};

export function KnowledgeMapPreview({ knowledgeMap, progress }: KnowledgeMapPreviewProps) {
  return (
    <Panel
      description="The knowledge map is the handoff from assessment to curriculum generation."
      elevated={Boolean(knowledgeMap)}
      title="Knowledge Map"
    >
      {knowledgeMap ? (
        <div className={styles.stack}>
          <div className={styles.feedbackHeader}>
            <StatusBadge tone="info">Recommended {knowledgeMap.recommended_level}</StatusBadge>
            <strong>{Math.round(knowledgeMap.confidence_score * 100)}% confidence</strong>
          </div>
          <div className={styles.mapGrid}>
            <MapColumn label="Strong" items={knowledgeMap.strong} />
            <MapColumn label="Weak" items={knowledgeMap.weak} />
            <MapColumn label="Missing" items={knowledgeMap.missing} />
          </div>
          {knowledgeMap.assessment_notes.length > 0 ? (
            <div className={styles.stack}>
              <span className={styles.metricLabel}>Assessment notes</span>
              <ul className={styles.noteList}>
                {knowledgeMap.assessment_notes.map((note) => (
                  <li className={styles.note} key={note}>
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {progress ? (
            <p className={styles.hint}>
              Finalized after {progress.answered_count} answered question
              {progress.answered_count === 1 ? "" : "s"}.
            </p>
          ) : null}
        </div>
      ) : (
        <span className={styles.empty}>
          Finalize the assessment after at least one answer to create the knowledge map.
        </span>
      )}
    </Panel>
  );
}

function MapColumn({ items, label }: { items: string[]; label: string }) {
  return (
    <div className={styles.mapColumn}>
      <h3>{label}</h3>
      <div className={styles.mapGroup}>
        {items.length > 0 ? (
          items.map((item) => (
            <span className={styles.chip} key={`${label}-${item}`}>
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
