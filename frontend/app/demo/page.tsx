import { NoAuthDemoFlow } from "@/components/demo/NoAuthDemoFlow";
import { AppShell } from "@/components/layout";
import { WorkflowStepper } from "@/components/workflow";

export default function DemoPage() {
  return (
    <AppShell
      activeItem="demo"
      eyebrow="PathAI local no-auth demo"
      subtitle="A guided backend-backed workflow for assessment, curriculum, resources, critic review, progress, quiz, adaptation, evaluation, and orchestration."
      title="Working Flow"
    >
      <WorkflowStepper
        description="The demo runs these services in sequence while the future product screens remain staged in the navigation."
        title="Demo execution path"
        variant="compact"
      />
      <NoAuthDemoFlow embedded />
    </AppShell>
  );
}
