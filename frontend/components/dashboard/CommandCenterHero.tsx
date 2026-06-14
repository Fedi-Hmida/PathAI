import Link from "next/link";

import styles from "./CommandCenterDashboard.module.css";

type CommandCenterHeroProps = {
  goal: string;
  level: string;
  mastery: number;
  subtitle: string;
  weekLabel: string;
};

export function CommandCenterHero({
  goal,
  level,
  mastery,
  subtitle,
  weekLabel
}: CommandCenterHeroProps) {
  return (
    <section className={styles.hero} aria-labelledby="command-center-goal">
      <div className={styles.heroCopy}>
        <div className={styles.heroMeta}>
          <span className={styles.metaPill}>Level: {level}</span>
          <span className={styles.mutedPill}>{weekLabel}</span>
        </div>
        <h2 id="command-center-goal">{goal}</h2>
        <p>{subtitle}</p>
        <div className={styles.heroActions}>
          <Link className={styles.primaryAction} href="/learn/new">
            Continue Path
          </Link>
          <Link className={styles.secondaryAction} href="/demo">
            View Backend Demo
          </Link>
        </div>
      </div>
      <ProgressRing value={mastery} />
    </section>
  );
}

function ProgressRing({ value }: { value: number }) {
  const radius = 58;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className={styles.progressWrap} aria-label={`Global mastery ${value} percent`}>
      <div className={styles.progressRing}>
        <svg aria-hidden="true" viewBox="0 0 140 140">
          <circle
            cx="70"
            cy="70"
            fill="transparent"
            r={radius}
            stroke="#f1f5f9"
            strokeWidth="9"
          />
          <circle
            cx="70"
            cy="70"
            fill="transparent"
            r={radius}
            stroke="#2563eb"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            strokeWidth="9"
          />
        </svg>
        <span className={styles.progressValue}>
          {value}
          <span>%</span>
        </span>
      </div>
      <span className={styles.progressLabel}>Global mastery</span>
    </div>
  );
}
