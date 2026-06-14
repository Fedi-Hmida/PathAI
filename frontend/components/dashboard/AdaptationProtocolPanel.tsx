import styles from "./CommandCenterDashboard.module.css";

type AdaptationProtocolPanelProps = {
  after: string;
  before: string;
  message: string;
  trigger: string;
};

export function AdaptationProtocolPanel({
  after,
  before,
  message,
  trigger
}: AdaptationProtocolPanelProps) {
  return (
    <section className={styles.inspectorSection} aria-labelledby="adaptation-protocol-title">
      <h2 className={styles.inspectorTitle} id="adaptation-protocol-title">
        Adaptation Protocol
      </h2>
      <article className={styles.adaptationCard}>
        <span className={styles.adaptationTrigger}>{trigger}</span>
        <p className={styles.adaptationText}>{message}</p>
        <div className={styles.beforeAfter}>
          <div>
            <span className={styles.columnTitle}>Before</span>
            <div className={styles.planBox}>{before}</div>
          </div>
          <span className={styles.arrowText} aria-hidden="true">
            -&gt;
          </span>
          <div>
            <span className={styles.columnTitle}>After</span>
            <div className={`${styles.planBox} ${styles.planBoxActive}`}>{after}</div>
          </div>
        </div>
        <button className={styles.approveButton} type="button">
          Approve New Plan
        </button>
      </article>
    </section>
  );
}
