export type CassetteType = 'malaria' | 'covid' | 'pregnancy' | 'hiv';

export type QualityFailure =
  | 'too_blurry'
  | 'too_dark'
  | 'too_bright'
  | 'cassette_not_found'
  | 'result_window_obscured';

export interface ImageQuality {
  blur_score: number;
  exposure_ok: boolean;
  cassette_detected: boolean;
  acceptable: boolean;
  failure_reason: QualityFailure | null;
}

export interface BoundingBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface LineReading {
  control_line_present: boolean;
  test_line_present: boolean;
  test_line_intensity: 'strong' | 'faint' | 'absent';
  confidence: number;
  raw_observation: string;
}

export interface ReadResult {
  outcome: 'positive' | 'negative' | 'invalid';
  confidence: number;
  invalid_reason: string | null;
  lines: LineReading;
  explanation: string;
}

export interface ReadResponse {
  request_id: string;
  timestamp: string;
  cassette_type: CassetteType;
  quality: ImageQuality;
  result: ReadResult;
  protocol: Record<string, unknown> | null;
  recommendation: string;
}

export interface AssistantMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AssistantMessageWithSources extends AssistantMessage {
  sources?: string[];
}

export interface AssistantRequest {
  message: string;
  scan_context: ReadResponse;
  history: AssistantMessage[];
}

export interface AssistantResponse {
  message: string;
  sources: string[];
}

export interface DetectResponse {
  detected: boolean;
  bbox: BoundingBox | null;
}
