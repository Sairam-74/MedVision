import { apiClient } from './client';

export interface ResearchMetrics {
  mean_positive_dice: number;
  mean_positive_iou: number;
  case_sensitivity: number;
  normal_false_positive_rate: number;
  case_true_positive: number;
  case_false_negative: number;
  case_false_positive: number;
  case_true_negative: number;
}
export interface ResearchStatus {
  updatedAt: string;
  dataset: { available: boolean; total: number; train: number; validation: number; test: number; version: string; quarantined: number; patientIndependenceVerified: boolean };
  runs: Array<{ id: string; label: string; status: string; epoch: number; batch?: number; batches?: number; dataset: string; epochs: Array<{ epoch: number; dice: number; sensitivity: number; falsePositiveRate: number }> }>;
  queueStatus: string;
  historical: ResearchMetrics | null;
  development: ResearchMetrics | null;
  delivery: { model: string; threshold: number; finalModelFrozen: boolean; reservedTestEvaluated: boolean; priorCheckpointExposure: string };
  limits: string[];
}
export async function fetchResearchStatus(): Promise<ResearchStatus> {
  return (await apiClient.get<ResearchStatus>('/api/research')).data;
}
