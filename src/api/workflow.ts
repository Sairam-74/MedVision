import { apiClient } from './client';
import type { PredictionResult, Analysis } from '@/types';
export interface Patient {
  id: string;
  identifier: string;
  name: string;
  age: number | null;
  gender: string;
  created_at: string;
}
export interface StudyImage {
  id: string;
  view_type: string;
  analysis_id: string;
  uploaded_at: string;
  analysis: Analysis;
  result: PredictionResult | null;
  error: string | null;
}
export interface ReportVersion {
  revision: number;
  snapshot: string;
  author_id: string;
  created_at: string;
}
export interface Report {
  id: string;
  revision: number;
  status: string;
  findings: string;
  impression: string;
  ai_decision: string;
  corrections: string;
  updated_at: string;
  finalized_at: string | null;
  versions: ReportVersion[];
}
export interface Study {
  id: string;
  patient: Patient;
  examination_date: string;
  body_part: string;
  laterality: string;
  clinical_history: string;
  referring_physician: string;
  created_at: string;
  images: StudyImage[];
  report: Report | null;
}
export interface StudySummary {
  id: string;
  patient_name: string;
  patient_identifier: string;
  examination_date: string;
  body_part: string;
  laterality: string;
  report_status: string | null;
  images: { view_type: string; analysis_id: string; status: string }[];
}
export interface Feedback {
  id: string;
  correct: number;
  category: string;
  comments: string;
  confirmed: number;
  created_at: string;
  confirmed_at: string | null;
  has_corrected_mask: boolean;
}
export const patients = async (q: string) =>
  (await apiClient.post<Patient[]>('/patients/search', { q })).data;
export const createPatient = async (data: {
  name: string;
  identifier: string;
  age: number | null;
  gender: string;
}) => (await apiClient.post<Patient>('/patients', data)).data;
export const createStudy = async (data: {
  patient_id: string;
  examination_date: string;
  body_part: string;
  laterality: string;
  clinical_history: string;
  referring_physician: string;
}) => (await apiClient.post<Study>('/studies', data)).data;
export const getStudy = async (id: string) =>
  (await apiClient.get<Study>(`/studies/${id}`)).data;
export const searchStudies = async (params: Record<string, string | number>) =>
  (
    await apiClient.post<{
      items: StudySummary[];
      total: number;
      offset: number;
      limit: number;
    }>('/studies/search', params)
  ).data;
export const uploadView = async (id: string, view: string, file: File) => {
  const form = new FormData();
  form.append('image', file);
  form.append('view_type', view);
  return (
    await apiClient.post<{ analysisId: string }>(
      `/studies/${id}/images`,
      form,
      { timeout: 30000 },
    )
  ).data;
};
export const generateReport = async (id: string) =>
  (await apiClient.post<Report>(`/studies/${id}/report/generate`)).data;
export const saveReport = async (
  id: string,
  report: Report,
  action: string,
  corrections: Record<string, string>,
) =>
  (
    await apiClient.post<Report>(`/studies/${id}/report/${action}`, {
      revision: report.revision,
      findings: report.findings,
      impression: report.impression,
      ai_decision: report.ai_decision,
      corrections,
    })
  ).data;
export const feedbackList = async (id: string) =>
  (await apiClient.get<Feedback[]>(`/analyses/${id}/feedback`)).data;
export const submitFeedback = async (
  id: string,
  data: {
    correct: boolean;
    category: string;
    comments: string;
    corrected_findings: Record<string, string>;
  },
) => (await apiClient.post<Feedback>(`/analyses/${id}/feedback`, data)).data;
export const uploadCorrection = async (id: string, file: File) => {
  const form = new FormData();
  form.append('mask', file);
  return (
    await apiClient.post(`/feedback/${id}/mask`, form, { timeout: 30000 })
  ).data;
};
export const confirmCorrection = async (
  id: string,
  fracture: boolean,
  consent: boolean,
  partition: boolean,
) =>
  (
    await apiClient.post(`/feedback/${id}/confirm`, {
      fracture_present: fracture,
      training_consent: consent,
      training_partition_verified: partition,
    })
  ).data;
export function errorMessage(error: unknown) {
  const e = error as { response?: { data?: { detail?: unknown } } };
  return typeof e.response?.data?.detail === 'string'
    ? e.response.data.detail
    : 'Operation failed. Check access, input and service availability.';
}
