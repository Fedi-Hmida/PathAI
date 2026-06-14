import { AssessmentWorkspace } from "@/components/assessment";
import { AppShell } from "@/components/layout";

export default function NewLearningPathPage() {
  return (
    <AppShell
      activeItem="assessment"
      eyebrow="PathAI assessment"
      subtitle="Start with learner goals, answer diagnostic questions manually, and finalize a knowledge map before curriculum generation."
      title="Goal Intake"
    >
      <AssessmentWorkspace />
    </AppShell>
  );
}
