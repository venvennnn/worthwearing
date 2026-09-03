import type {
  AnalysisResult,
  DemoPayload,
  HealthResponse,
  ScenarioResult,
  TryOnJob,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getDemo() {
  return request<DemoPayload>("/api/demo");
}

export function getHealth() {
  return request<HealthResponse>("/health");
}

export function analyzeCandidate(candidateId: string) {
  return request<AnalysisResult>("/api/analyze", {
    method: "POST",
    body: JSON.stringify({ candidate_id: candidateId }),
  });
}

export function startTryOn(candidateId: string, shopperAssetId: string) {
  return request<TryOnJob>("/api/try-on", {
    method: "POST",
    body: JSON.stringify({
      candidate_id: candidateId,
      shopper_asset_id: shopperAssetId,
    }),
  });
}

export function getTryOn(jobId: string) {
  return request<TryOnJob>(`/api/try-on/${jobId}`);
}

export function requestPreparedFallback(jobId: string) {
  return request<TryOnJob>(`/api/try-on/${jobId}/fallback`, { method: "POST" });
}

export function createScenarios(candidateId: string, tryOnJobId?: string) {
  return request<ScenarioResult>("/api/scenarios", {
    method: "POST",
    body: JSON.stringify({
      candidate_id: candidateId,
      try_on_job_id: tryOnJobId,
    }),
  });
}
