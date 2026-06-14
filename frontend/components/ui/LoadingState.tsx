import styles from "./ui.module.css";

type LoadingStateProps = {
  message?: string;
  title?: string;
};

export function LoadingState({
  message = "Preparing the next PathAI step.",
  title = "Loading"
}: LoadingStateProps) {
  return (
    <div aria-live="polite" className={styles.state} role="status">
      <div className={styles.stateContent}>
        <h2 className={styles.stateTitle}>{title}</h2>
        <p className={styles.stateMessage}>{message}</p>
      </div>
    </div>
  );
}
