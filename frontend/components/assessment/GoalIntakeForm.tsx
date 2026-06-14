import { Button, Panel, SelectField, TextArea, TextField } from "@/components/ui";
import type { DifficultyLevel, GoalIntakeRequest } from "@/lib/api/assessment";

import styles from "./Assessment.module.css";

export type GoalIntakeFormValue = Required<
  Pick<GoalIntakeRequest, "goal" | "hours_per_week" | "max_questions" | "target_level" | "timeline_weeks">
>;

type GoalIntakeFormProps = {
  disabled?: boolean;
  isLoading?: boolean;
  onChange: (value: GoalIntakeFormValue) => void;
  onSubmit: () => void;
  value: GoalIntakeFormValue;
};

const targetLevelOptions = [
  { label: "Beginner", value: "beginner" },
  { label: "Intermediate", value: "intermediate" },
  { label: "Advanced", value: "advanced" }
];

export function GoalIntakeForm({
  disabled = false,
  isLoading = false,
  onChange,
  onSubmit,
  value
}: GoalIntakeFormProps) {
  const canSubmit = value.goal.trim().length >= 3 && !disabled && !isLoading;

  return (
    <Panel
      description="Define the learning target. PathAI will use this to choose diagnostic questions."
      elevated
      title="Goal Intake"
    >
      <form
        className={styles.stack}
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
      >
        <TextArea
          disabled={disabled || isLoading}
          hint="Example: Learn RAG systems for a graduation project."
          label="Learning goal"
          onChange={(event) => onChange({ ...value, goal: event.target.value })}
          rows={5}
          value={value.goal}
        />
        <div className={styles.fieldGrid}>
          <TextField
            disabled={disabled || isLoading}
            label="Timeline weeks"
            max={52}
            min={1}
            onChange={(event) =>
              onChange({ ...value, timeline_weeks: Number(event.target.value) })
            }
            type="number"
            value={value.timeline_weeks}
          />
          <TextField
            disabled={disabled || isLoading}
            label="Hours per week"
            max={80}
            min={1}
            onChange={(event) => onChange({ ...value, hours_per_week: Number(event.target.value) })}
            type="number"
            value={value.hours_per_week}
          />
        </div>
        <div className={styles.fieldGrid}>
          <SelectField
            disabled={disabled || isLoading}
            label="Target level"
            onChange={(event) =>
              onChange({ ...value, target_level: event.target.value as DifficultyLevel })
            }
            options={targetLevelOptions}
            value={value.target_level}
          />
          <TextField
            disabled={disabled || isLoading}
            hint="The backend supports 3 to 12 questions."
            label="Question limit"
            max={12}
            min={3}
            onChange={(event) => onChange({ ...value, max_questions: Number(event.target.value) })}
            type="number"
            value={value.max_questions}
          />
        </div>
        <Button disabled={!canSubmit} fullWidth isLoading={isLoading} size="lg" type="submit">
          Start Assessment
        </Button>
      </form>
    </Panel>
  );
}
