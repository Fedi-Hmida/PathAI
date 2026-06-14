import { useId, type InputHTMLAttributes } from "react";

import { classNames } from "./classNames";
import styles from "./ui.module.css";

type FieldSize = "sm" | "md" | "lg";

type TextFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "size"> & {
  error?: string;
  hint?: string;
  label: string;
  size?: FieldSize;
};

const sizeClass: Record<FieldSize, string> = {
  sm: styles.controlSm,
  md: styles.controlMd,
  lg: styles.controlLg
};

export function TextField({
  className,
  error,
  hint,
  id,
  label,
  size = "md",
  ...props
}: TextFieldProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const descriptionId = error || hint ? `${inputId}-description` : undefined;

  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={inputId}>
        {label}
      </label>
      <input
        aria-describedby={descriptionId}
        aria-invalid={Boolean(error)}
        className={classNames(
          styles.control,
          sizeClass[size],
          error && styles.controlError,
          className
        )}
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
