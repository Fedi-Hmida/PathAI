import { redirect } from "next/navigation";

import { DEMO_RUN_ID } from "@/lib/types/orchestration";

export default function Home() {
  redirect(`/dashboard/${DEMO_RUN_ID}`);
}
