import { requestJson } from "./client";

export type EvaluationDatasetSummary = {
  dataset_name: string;
  goal: string;
  hours_per_week: number;
  timeline_weeks: number;
};

export type EvaluationDatasetsResponse = {
  datasets: EvaluationDatasetSummary[];
};

export type EvaluationRubricSummary = {
  dimensions?: unknown[];
  name?: string;
  rubric_id?: string;
};

export type EvaluationRubricsResponse = {
  rubrics: EvaluationRubricSummary[];
};

export function getEvaluationDatasets(): Promise<EvaluationDatasetsResponse> {
  return requestJson<EvaluationDatasetsResponse>("/evaluation/datasets");
}

export function getEvaluationRubrics(): Promise<EvaluationRubricsResponse> {
  return requestJson<EvaluationRubricsResponse>("/evaluation/rubrics");
}
