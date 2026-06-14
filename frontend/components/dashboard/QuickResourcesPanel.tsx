import type { QuickResource } from "@/lib/dashboard/types";

import styles from "./CommandCenterDashboard.module.css";

type QuickResourcesPanelProps = {
  resources: QuickResource[];
};

export function QuickResourcesPanel({ resources }: QuickResourcesPanelProps) {
  return (
    <section className={styles.inspectorSection} aria-labelledby="quick-resources-title">
      <h2 className={styles.inspectorTitle} id="quick-resources-title">
        Quick Resources
      </h2>
      <div className={styles.quickResourceList}>
        {resources.map((resource) => (
          <article className={styles.quickResource} key={resource.label}>
            <div>
              <strong>{resource.label}</strong>
              <span>{resource.meta}</span>
            </div>
            <button type="button">{resource.action}</button>
          </article>
        ))}
      </div>
    </section>
  );
}
