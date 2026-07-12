import { apiGet, apiPost, ApiError } from "@/lib/api/client";
import type {
  AssessmentAnswerCreate,
  AssessmentAnswerDTO,
  AssessmentAnswerResponse,
  AssessmentSessionDTO,
} from "@/lib/types/assessment";

export function getAssessment(assessmentId: string): Promise<AssessmentSessionDTO> {
  return apiGet<AssessmentSessionDTO>(`/assessments/${assessmentId}`);
}

export function getAssessmentAnswers(assessmentId: string): Promise<AssessmentAnswerDTO[]> {
  return apiGet<AssessmentAnswerDTO[]>(`/assessments/${assessmentId}/answers`);
}

export async function getMyAssessment(): Promise<AssessmentSessionDTO | null> {
  try {
    return await apiGet<AssessmentSessionDTO>("/me/assessment");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export function startAssessment(): Promise<AssessmentSessionDTO> {
  return apiPost<AssessmentSessionDTO>("/me/assessment/start");
}

export function submitAssessmentAnswer(
  assessmentId: string,
  payload: AssessmentAnswerCreate
): Promise<AssessmentAnswerResponse> {
  return apiPost<AssessmentAnswerResponse>(`/me/assessment/${assessmentId}/answer`, payload);
}
