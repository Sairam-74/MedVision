import { apiClient } from './client';
import type { Analysis, AnalysisStatusResponse, CreateAnalysisResponse, PredictionResult } from '@/types';

export async function fetchAnalyses() {
  const { data } = await apiClient.get<Analysis[]>('/analyses');
  return data;
}

export async function fetchAnalysisById(analysisId: string) {
  const { data } = await apiClient.get<PredictionResult>(`/analyses/${analysisId}`);
  return data;
}

export async function createAnalysis(file: File) {
  const formData = new FormData();
  formData.append('image', file);
  const { data } = await apiClient.post<CreateAnalysisResponse>('/analyses', formData);
  return data;
}

export async function fetchAnalysisStatus(analysisId: string) {
  const { data } = await apiClient.get<AnalysisStatusResponse>(`/analyses/${analysisId}/status`);
  return data;
}
