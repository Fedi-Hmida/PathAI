import { apiGet } from "@/lib/api/client";
import type { LearningGoalDTO } from "@/lib/types/goal";

export function getGoal(goalId: string): Promise<LearningGoalDTO> {
  return apiGet<LearningGoalDTO>(`/goals/${goalId}`);
}
