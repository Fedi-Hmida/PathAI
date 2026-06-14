import { useId, type SelectHTMLAttributes } from "react";

import { classNames } from "./classNames";
import styles from "./ui.module.css";

type SelectOption = {
  label: string;
  value: string;
};

type SelectFieldProps = Omit<SelectHTMLAttributes<HTMLSelectElement>, "children"> & {
  error?: string;
  hint?: string;
  label: string;
  options: SelectOption[];
};

export function SelectField({
  className,
  error,
  hint,
  id,
  label,
  options,
  ...props
}: SelectFieldProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const descriptionId = error || hint ? `${inputId}-description` : undefined;

  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={inputId}>
        {label}
      </label>
      <select
        aria-describedby={descriptionId}
        aria-invalid={Boolean(error)}
        className={classNames(styles.control, styles.controlMd, error && styles.controlError, className)}
        id={inputId}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
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
