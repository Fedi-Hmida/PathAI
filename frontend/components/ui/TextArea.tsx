import { useId, type TextareaHTMLAttributes } from "react";

import { classNames } from "./classNames";
import styles from "./ui.module.css";

type TextAreaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  error?: string;
  hint?: string;
  label: string;
};

export function TextArea({ className, error, hint, id, label, ...props }: TextAreaProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const descriptionId = error || hint ? `${inputId}-description` : undefined;

  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={inputId}>
        {label}
      </label>
      <textarea
        aria-describedby={descriptionId}
        aria-invalid={Boolean(error)}
        className={classNames(styles.control, styles.controlMd, error && styles.controlError, className)}
        id={inputId}
        {...props}
      />
      {error ? (
        <p className={styles.fieldError} id={descriptionId}>
          {error}
        </p>
      ) : hint ? (
        <p className={styles.fieldHint} id={descriptionId}>
          {hint}
        </p>
      ) : null}
    </div>
  );
}
