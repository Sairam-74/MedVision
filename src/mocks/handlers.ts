import { http, HttpResponse, delay } from 'msw';
import { mockAnalyses, mockAuditLogs, mockPredictionResults, mockSession, mockUsers } from './data';
import type { Analysis, AnalysisStatusResponse, PredictionResult } from '@/types';

const analyses = [...mockAnalyses];
const predictionResults: Record<string, PredictionResult> = { ...mockPredictionResults };
const jobPollCounts: Record<string, number> = {};

function createMockResult(analysis: Analysis): PredictionResult {
  return {
    id: `res-${analysis.id}`,
    analysisId: analysis.id,
    fractureStatus: 'fracture',
    severity: 'moderate',
    confidence: 0.86,
    region: 'Uploaded X-ray',
    type: 'Suspected cortical discontinuity',
    recommendation: 'Review the highlighted region and correlate with clinical findings.',
    imageUrl: '/mock_xray.png',
    originalImageUrl: '/mock_xray.png',
    overlayUrl: '/segmentation_overlay_prediction.png',
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
    },
    disclaimer: 'AI-assisted result — requires clinician review before clinical use.',
  };
}

export const handlers = [
  http.post('*/auth/login', async () => {
    await delay(350);
    return HttpResponse.json(mockSession);
  }),
  http.post('*/auth/refresh', async () => {
    await delay(150);
    return HttpResponse.json(mockSession);
  }),
  http.post('*/auth/signup', async () => HttpResponse.json({ message: 'Account created successfully.' })),
  http.post('*/auth/request-access', async () => HttpResponse.json({ message: 'Account created successfully.' })),
  http.post('*/auth/forgot-password', async () => HttpResponse.json({ message: 'Password reset email sent.' })),
  http.post('*/auth/reset-password', async () => HttpResponse.json({ message: 'Password has been reset.' })),
  http.post('*/analyses', async () => {
    await delay(50);
    const analysisId = `ana-${Date.now()}`;
    const analysis: Analysis = {
      id: analysisId,
      uploader: mockSession.user.name,
      createdAt: new Date().toISOString(),
      status: 'queued',
      fileName: 'uploaded-xray.png',
      uploadedBy: mockSession.user.role,
    };
    analyses.unshift(analysis);
    predictionResults[analysisId] = createMockResult(analysis);
    jobPollCounts[analysisId] = 0;

    return HttpResponse.json({
      analysisId,
      status: 'queued',
      message: 'Analysis queued for prediction.',
    });
  }),
  http.get('*/analyses', async () => HttpResponse.json(analyses)),
  http.get('*/analyses/:analysisId/status', async ({ params }) => {
    await delay(50);
    const analysisId = String(params.analysisId);
    const analysis = analyses.find((item) => item.id === analysisId);
    if (!analysis) {
      return HttpResponse.json({ message: 'Not found' }, { status: 404 });
    }

    jobPollCounts[analysisId] = (jobPollCounts[analysisId] ?? 0) + 1;
    const pollCount = jobPollCounts[analysisId];
    let status: AnalysisStatusResponse['status'] = 'queued';
    let progress = 35;

    if (pollCount >= 3) {
      status = 'completed';
      progress = 100;
    } else if (pollCount >= 2) {
      status = 'processing';
      progress = 70;
    }

    analysis.status = status;
    return HttpResponse.json({
      analysisId,
      status,
      progress,
      result: status === 'completed' ? predictionResults[analysisId] : undefined,
    });
  }),
  http.get('*/analyses/:analysisId', async ({ params }) => {
    const analysisId = String(params.analysisId);
    const result = predictionResults[analysisId];
    if (!result) {
      return HttpResponse.json({ message: 'Not found' }, { status: 404 });
    }
    return HttpResponse.json(result);
  }),
  http.get('*/users', async () => HttpResponse.json(mockUsers)),
  http.get('*/audit-logs', async () => HttpResponse.json(mockAuditLogs)),
];
