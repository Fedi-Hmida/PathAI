import { classNames } from "@/components/ui/classNames";
import type { ResourceCard } from "@/lib/dashboard/types";

import styles from "./CommandCenterDashboard.module.css";

type RecommendedResourcesProps = {
  resources: ResourceCard[];
};

const resourceToneClass: Record<ResourceCard["tone"], string> = {
  amber: styles.resourceAmber,
  indigo: styles.resourceIndigo,
  teal: styles.resourceTeal
};

export function RecommendedResources({ resources }: RecommendedResourcesProps) {
  return (
    <section className={styles.resources} aria-labelledby="recommended-resources-title">
      <header className={styles.cardHeader}>
        <div className={styles.resourceHeaderMeta}>
          <h2 className={styles.cardTitle} id="recommended-resources-title">
            Curated Learning Materials
          </h2>
          <span className={styles.miniLegend}>
            Source diversity:
            <span className={styles.diversityDots} aria-hidden="true">
              <span />
              <span />
              <span />
            </span>
            <strong>Optimal</strong>
          </span>
        </div>
        <span className={styles.mutedPill}>Library refresh</span>
      </header>
      <div className={styles.resourcesGrid}>
        {resources.map((resource) => (
          <article
            className={classNames(styles.resourceCard, resourceToneClass[resource.tone])}
            key={resource.title}
          >
            <div className={styles.resourceTop}>
              <span className={styles.resourceIcon}>{resource.kind.slice(0, 2).toUpperCase()}</span>
              <span className={styles.resourceKind}>
                {resource.kind} - {resource.source}
              </span>
            </div>
            <div>
              <h3>{resource.title}</h3>
              <p>{resource.summary}</p>
            </div>
            <div className={styles.resourceFooter}>
              <span className={styles.resourceDifficulty}>{resource.difficulty}</span>
              <span className={styles.resourceRating}>{resource.rating}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
