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

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, text);
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
