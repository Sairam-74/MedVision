import type { Analysis, AuditLogEntry, AuthSession, PredictionResult, AppUser } from '@/types';

export const mockUser: AppUser = {
  id: 'user-1',
  name: 'Demo Clinician',
  email: 'demo.clinician@example.invalid',
  role: 'clinician',
  status: 'active',
  organization: 'Demo Imaging Organization',
};

export const mockSession: AuthSession = {
  user: mockUser,
  accessToken: 'mock-access-token',
  expiresAt: new Date(Date.now() + 1000 * 60 * 15).toISOString(),
};

export const mockAnalyses: Analysis[] = [
  {
    id: 'ana-1001',
    uploader: 'Alex Chen',
    createdAt: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    status: 'completed',
    fileName: 'xray-left-ankle.png',
    uploadedBy: 'technician',
    patientLabel: 'MRN-20491',
  },
  {
    id: 'ana-1002',
    uploader: 'Demo Clinician',
    createdAt: new Date(Date.now() - 1000 * 60 * 68).toISOString(),
    status: 'processing',
    fileName: 'wrist-ap.png',
    uploadedBy: 'clinician',
  },
  {
    id: 'ana-1003',
    uploader: 'Alex Chen',
    createdAt: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
    status: 'queued',
    fileName: 'pelvis-01.jpg',
    uploadedBy: 'technician',
  },
];

export const mockPredictionResults: Record<string, PredictionResult> = {
  'ana-1001': {
    id: 'res-2001',
    analysisId: 'ana-1001',
    fractureStatus: 'fracture',
    severity: 'moderate',
    confidence: 0.93,
    region: 'Left distal fibula',
    type: 'Oblique fracture',
    recommendation: 'Review with orthopedics and correlate with patient exam.',
    overlayUrl: '/segmentation_overlay_prediction.png',
    imageUrl: '/mock_xray.png',
    originalImageUrl: '/mock_xray.png',
    maskPngBase64:
      'iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAAAAAB5Gfe6AAAB+klEQVR4AeXBUUoEURDAwOT+h24VEVZd...',
    maskShape: [256, 256],
    calibratedThreshold: 0.9,
    severityFeatures: {
      area: 387.0,
      perimeter: 101.2548,
      compactness: 0.4743,
      aspectRatio: 1.7273,
    },
    metrics: {
      dice: 0.4526,
      iou: 0.2925,
      precision: 0.41,
      recall: 0.51,
    },
    disclaimer: 'AI-assisted result — requires clinician review before clinical use.',
    reviewedByRole: 'clinician',
  },
  'ana-1002': {
    id: 'res-2002',
    analysisId: 'ana-1002',
    fractureStatus: 'needs_review',
    severity: 'low',
    confidence: 0.68,
    region: 'Right wrist',
    type: 'Potential cortical irregularity',
    recommendation: 'Second-reader review recommended due to motion artifact.',
    imageUrl: '/mock_xray.png',
    originalImageUrl: '/mock_xray.png',
    calibratedThreshold: 0.9,
    disclaimer: 'AI-assisted result — requires clinician review before clinical use.',
  },
  'ana-1003': {
    id: 'res-2003',
    analysisId: 'ana-1003',
    fractureStatus: 'no_fracture',
    severity: 'low',
    confidence: 0.88,
    region: 'Pelvis',
    type: 'No acute fracture pattern detected',
    recommendation: 'No acute osseous abnormality identified by the model.',
    imageUrl: '/mock_xray.png',
    originalImageUrl: '/mock_xray.png',
    calibratedThreshold: 0.9,
    severityFeatures: {
      area: 0.0,
      perimeter: 0.0,
      compactness: 0.0,
      aspectRatio: 0.0,
    },
    disclaimer: 'AI-assisted result — requires clinician review before clinical use.',
  },
};

export const mockUsers: AppUser[] = [
  mockUser,
  { id: 'user-2', name: 'Alex Chen', email: 'alex.chen@example.invalid', role: 'technician', status: 'active', organization: 'Demo Imaging Organization' },
  { id: 'user-3', name: 'Sana Iqbal', email: 'sana.iqbal@example.invalid', role: 'admin', status: 'pending', organization: 'Demo Imaging Organization' },
  { id: 'user-4', name: 'Noah Brooks', email: 'noah.brooks@example.invalid', role: 'clinician', status: 'suspended', organization: 'Demo Imaging Organization' },
];

export const mockAuditLogs: AuditLogEntry[] = [
  {
    id: 'audit-1',
    userName: 'Alex Chen',
    userRole: 'technician',
    action: 'uploaded',
    analysisId: 'ana-1001',
    createdAt: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    details: 'Uploaded left ankle image.',
  },
  {
    id: 'audit-2',
    userName: 'Demo Clinician',
    userRole: 'clinician',
    action: 'viewed',
    analysisId: 'ana-1001',
    createdAt: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
  },
  {
    id: 'audit-3',
    userName: 'Demo Clinician',
    userRole: 'clinician',
    action: 'approved',
    analysisId: 'ana-1001',
    createdAt: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
  },
];
