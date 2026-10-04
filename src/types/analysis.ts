import type { UserRole } from './auth';

export type AnalysisStatus = 'queued' | 'processing' | 'completed' | 'failed' | 'timed_out';
export type PredictionStatus = 'fracture' | 'no_fracture' | 'needs_review';

export interface Analysis {
  id: string;
  uploader: string;
  createdAt: string;
  status: AnalysisStatus;
  fileName: string;
  patientLabel?: string;
  uploadedBy: string;
}

export interface PredictionResult {
  id: string;
  analysisId: string;
  fractureStatus: PredictionStatus;
  severity: 'low' | 'moderate' | 'high' | 'critical';
  confidence: number;
  region: string;
  type: string;
  recommendation: string;
  overlayUrl?: string;
  imageUrl: string;
  originalImageUrl?: string;
  maskPngBase64?: string;
  maskShape?: [number, number];
  calibratedThreshold?: number;
  severityFeatures?: {
    area: number;
    perimeter: number;
    compactness: number;
    aspectRatio: number;
  };
  metrics?: {
    dice?: number | null;
    iou?: number | null;
    precision?: number | null;
    recall?: number | null;
  };
  reportUrl?: string;
  disclaimer: string;
  reviewedByRole?: UserRole;
}

export interface CreateAnalysisResponse {
  analysisId: string;
  status: AnalysisStatus;
  message: string;
}

export interface AnalysisStatusResponse {
  analysisId: string;
  status: AnalysisStatus;
  progress: number;
  result?: PredictionResult;
  errorMessage?: string;
}

export interface UploadValidationError {
  code: 'file_type' | 'file_size' | 'upload_failed' | 'timeout' | 'inference_error';
  message: string;
}
