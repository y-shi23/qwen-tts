export interface SynthesizeOptions {
  text: string;
  voice?: string;
  language?: string;
  outputPath?: string;
  download?: boolean;
}

export interface SynthesizeResult {
  success: boolean;
  message: string;
  audioUrl?: string;
  outputPath?: string;
}

export interface TTSRequest {
  text: string;
  voice?: string;
  language?: string;
}

export interface TTSResponse {
  success: boolean;
  message: string;
  file_url?: string;
  text: string;
  voice: string;
  language: string;
}

export interface TTSUrlResponse {
  success: boolean;
  message: string;
  audio_url?: string;
  text: string;
  voice: string;
  language: string;
  note: string;
}

export interface VoicesResponse {
  voices: string[];
  count: number;
}

export interface LanguagesResponse {
  languages: string[];
  count: number;
}

export interface QueueEstimation {
  rank: number;
  queue_size: number;
  rank_eta: number;
}

export interface SSEEventData {
  msg?: string;
  rank?: number;
  queue_size?: number;
  rank_eta?: number;
  output?: {
    data?: Array<{ url?: string }>;
  };
}
