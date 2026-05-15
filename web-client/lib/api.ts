import type { ReadResponse, AssistantRequest, AssistantResponse, DetectResponse } from './types';

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const BASE_HEADERS: Record<string, string> = BASE.includes('ngrok')
  ? { 'ngrok-skip-browser-warning': '1' }
  : {};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function extractErrorMessage(status: number, body: string): string {
  try {
    const json = JSON.parse(body);
    // FastAPI validation error: { detail: [{ msg, loc }] }
    if (Array.isArray(json.detail)) {
      return json.detail.map((e: { msg?: string }) => e.msg ?? 'Invalid input').join(', ');
    }
    // FastAPI HTTP exception: { detail: "string" }
    if (typeof json.detail === 'string') return json.detail;
    // slowapi rate limit: { error: "..." }
    if (typeof json.error === 'string') return json.error;
  } catch { /* not JSON */ }

  // Fallback by status code
  if (status === 429) return 'Too many requests — please wait a moment and try again.';
  if (status === 422) return 'The image could not be processed. Please try again.';
  if (status >= 500) return 'Server error — please try again in a few seconds.';
  return 'Something went wrong. Please try again.';
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new ApiError(res.status, extractErrorMessage(res.status, body));
  }
  return res.json() as Promise<T>;
}

export async function readCassette(image: File, cassetteType: string): Promise<ReadResponse> {
  const body = new FormData();
  body.append('image', image);
  body.append('cassette_type', cassetteType);
  const res = await fetch(`${BASE}/api/read`, { method: 'POST', headers: BASE_HEADERS, body });
  return handleResponse<ReadResponse>(res);
}

export async function detectCassette(image: Blob): Promise<DetectResponse> {
  const body = new FormData();
  body.append('image', image, 'frame.jpg');
  const res = await fetch(`${BASE}/api/detect-cassette`, { method: 'POST', headers: BASE_HEADERS, body });
  return handleResponse<DetectResponse>(res);
}

export async function sendMessage(request: AssistantRequest): Promise<AssistantResponse> {
  const res = await fetch(`${BASE}/api/assistant/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...BASE_HEADERS },
    body: JSON.stringify(request),
  });
  return handleResponse<AssistantResponse>(res);
}

export async function getHistory(): Promise<ReadResponse[]> {
  const res = await fetch(`${BASE}/api/results`, { headers: BASE_HEADERS });
  return handleResponse<ReadResponse[]>(res);
}
