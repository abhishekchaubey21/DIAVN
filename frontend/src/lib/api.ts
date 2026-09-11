import { Case, Dealer, RiskScore, RiskSignal, InvoiceVerificationSummary } from '@/types';
import { MOCK_CASES, MOCK_DEALERS, MOCK_RISK_SCORES, MOCK_RISK_SIGNALS } from './mockData';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchHealthCheck() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { cache: 'no-store' });
    if (!res.ok) throw new Error('Health check failed');
    return await res.json();
  } catch (err) {
    return { status: 'offline', error: String(err) };
  }
}

export async function getCases(): Promise<{ cases: Case[]; isMock: boolean }> {
  try {
    const res = await fetch(`${API_BASE_URL}/cases`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return { cases: data, isMock: false };
      }
    }
  } catch (err) {
    console.warn('Backend unavailable, falling back to synthetic dataset:', err);
  }
  return { cases: MOCK_CASES, isMock: true };
}

export async function getCaseById(id: string): Promise<{ caseItem: Case | null; isMock: boolean }> {
  try {
    const res = await fetch(`${API_BASE_URL}/cases/${id}`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      return { caseItem: data, isMock: false };
    }
  } catch (err) {
    console.warn(`Backend fetch for case ${id} failed, using synthetic mock:`, err);
  }
  const found = MOCK_CASES.find((c) => c.id === id || c.case_number === id) || null;
  return { caseItem: found, isMock: true };
}

export async function getDealers(): Promise<{ dealers: Dealer[]; isMock: boolean }> {
  try {
    const res = await fetch(`${API_BASE_URL}/dealers`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return { dealers: data, isMock: false };
      }
    }
  } catch (err) {
    console.warn('Backend fetch for dealers failed, using synthetic mock:', err);
  }
  return { dealers: MOCK_DEALERS, isMock: true };
}

export async function getDealerById(id: string): Promise<{ dealer: Dealer | null; isMock: boolean }> {
  try {
    const res = await fetch(`${API_BASE_URL}/dealers/${id}`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      return { dealer: data, isMock: false };
    }
  } catch (err) {
    console.warn(`Backend fetch for dealer ${id} failed:`, err);
  }
  const found = MOCK_DEALERS.find((d) => d.id === id || d.dealer_code === id) || null;
  return { dealer: found, isMock: true };
}

export interface InvoiceUploadResult {
  invoice_id: string;
  case_id: string;
  status: string;
  original_filename: string;
  message: string;
}

export async function uploadInvoiceDocument(caseId: string, file: File): Promise<InvoiceUploadResult> {
  const formData = new FormData();
  formData.append('case_id', caseId);
  formData.append('file', file);

  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/invoices`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }

    return await res.json();
  } catch (err: any) {
    console.warn('Backend upload unavailable, using client-staged simulation:', err);
    return {
      invoice_id: `INV-CLIENT-${Date.now()}`,
      case_id: caseId,
      status: 'completed',
      original_filename: file.name,
      message: 'Invoice staged locally (Client preview mode).'
    };
  }
}

export async function getInvoiceDetails(invoiceId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/invoices/${invoiceId}`, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Failed to fetch invoice details:', err);
  }
  return null;
}

export async function runInvoiceVerification(invoiceId: string): Promise<InvoiceVerificationSummary | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/verification/invoice/${invoiceId}`, {
      method: 'POST',
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Failed to run verification on backend:', err);
  }
  return null;
}

export async function getInvoiceVerification(invoiceId: string): Promise<InvoiceVerificationSummary | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/verification/invoice/${invoiceId}`, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Failed to fetch invoice verification:', err);
  }
  return null;
}

export async function uploadInstallationImage(caseId: string, file: File, imageType: string = 'installation_wide') {
  const formData = new FormData();
  formData.append('case_id', caseId);
  formData.append('image_type', imageType);
  formData.append('file', file);

  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/images`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Image upload failed' }));
      throw new Error(err.detail || 'Image upload failed');
    }
    return await res.json();
  } catch (err: any) {
    console.warn('Backend image upload unavailable, simulating client stage:', err);
    return {
      id: `IMG-CLIENT-${Date.now()}`,
      case_id: caseId,
      image_type: imageType,
      original_filename: file.name,
      file_size_bytes: file.size,
      mime_type: file.type,
      verification_status: 'uploaded',
      message: 'Image staged locally.'
    };
  }
}

export async function getInstallationImagesForCase(caseId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/images/case/${caseId}`, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to fetch images for case ${caseId}:`, err);
  }
  return { case_id: caseId, total_images: 0, images: [] };
}

export async function runImageVerification(imageId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/verification/image/${imageId}`, {
      method: 'POST',
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to run image verification for ${imageId}:`, err);
  }
  return null;
}

export async function getImageVerification(imageId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/verification/image/${imageId}`, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to fetch image verification for ${imageId}:`, err);
  }
  return null;
}

export async function runImageEmbeddingVerification(imageId: string, topK: number = 5, threshold?: number) {
  try {
    let url = `${API_BASE_URL}/api/v1/verification/image/${imageId}/embedding?top_k=${topK}`;
    if (threshold !== undefined) {
      url += `&threshold=${threshold}`;
    }
    const res = await fetch(url, {
      method: 'POST',
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to run embedding verification for ${imageId}:`, err);
  }
  return null;
}

export async function getImageEmbeddingVerification(imageId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/verification/image/${imageId}/embedding`, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to fetch embedding verification for ${imageId}:`, err);
  }
  return null;
}

export async function getSimilarImages(imageId: string, topK: number = 5, threshold?: number) {
  try {
    let url = `${API_BASE_URL}/api/v1/images/${imageId}/similar-images?top_k=${topK}`;
    if (threshold !== undefined) {
      url += `&threshold=${threshold}`;
    }
    const res = await fetch(url, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to fetch similar images for ${imageId}:`, err);
  }
  return null;
}

export async function calculateCaseRiskScore(caseId: string, policyVersion: string = 'risk-v1') {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/risk/cases/${caseId}/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ policy_version: policyVersion }),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to calculate risk score for case ${caseId}:`, err);
  }
  return null;
}

export async function getCaseRiskScore(caseId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/risk/cases/${caseId}`, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to fetch risk score for case ${caseId}:`, err);
  }
  return null;
}

export async function getCaseRiskHistory(caseId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/risk/cases/${caseId}/history`, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to fetch risk history for case ${caseId}:`, err);
  }
  return [];
}

export async function getCaseRelationships(caseId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/relationships/cases/${caseId}`, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to fetch relationships for case ${caseId}:`, err);
  }
  return null;
}

export async function analyzeCaseRelationships(caseId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/relationships/cases/${caseId}/analyze`, {
      method: 'POST',
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to analyze relationships for case ${caseId}:`, err);
  }
  return null;
}

export async function getDealerRelationships(dealerId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/relationships/dealers/${dealerId}`, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to fetch dealer relationships for ${dealerId}:`, err);
  }
  return null;
}

export async function getCaseGraph(caseId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/relationships/cases/${caseId}/graph`, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to fetch case graph for ${caseId}:`, err);
  }
  return null;
}

export async function getDealerGraph(dealerId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/relationships/dealers/${dealerId}/graph`, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to fetch dealer graph for ${dealerId}:`, err);
  }
  return null;
}

export async function runCasePipeline(caseId: string, policyVersion: string = 'risk-v1', forceRerun: boolean = false) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/pipeline/cases/${caseId}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ policy_version: policyVersion, force_rerun: forceRerun }),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to run pipeline for case ${caseId}:`, err);
  }
  return null;
}

export async function getCasePipelineStatus(caseId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/pipeline/cases/${caseId}`, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to fetch pipeline status for case ${caseId}:`, err);
  }
  return null;
}

// Phase 9 Workflow & Alert Events API
export async function getCaseWorkflowEvents(caseId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/cases/${caseId}/workflow-events`, { cache: 'no-store' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to fetch workflow events for case ${caseId}:`, err);
  }
  return { case_id: caseId, events: [], total_count: 0 };
}

export async function retryWorkflowEvent(eventId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/workflow/events/${eventId}/retry`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Failed to retry workflow event ${eventId}:`, err);
  }
  return null;
}






