// =============================================================
// src/services/api.ts
// =============================================================
//const BASE = "http://localhost:8000";// اذا بتشغلينه لوكال خليه localhost:8000
const BASE = "https://lassen-final-project-1.onrender.com";

export class APIError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

async function post<T>(path: string, body: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new APIError(0, `تعذر الاتصال بالسيرفر (${BASE})`);
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new APIError(res.status, err.detail ?? `خطأ ${res.status}`);
  }
  return res.json();
}

// ── كنوز الكلمات ──────────────────────────────────────────────

export interface MeaningEntry  { title: string; explanation: string; source: "siwar" | "gpt" }
export interface ExampleVerse  { verse: string; poet: string; source: "database" | "gpt" }

export interface TreasuresResponse {
  status:          "ok" | "error";
  word?:            string;
  plural?:          string;
  primary_meaning?: string;
  meanings?:        MeaningEntry[];
  poetic_usage?:    string;
  symbolism?:       string;
  example_verses?:  ExampleVerse[];
  simple_tip?:      string;
  confidence?:      "high" | "medium" | "low";
  siwar?:           { found: boolean; definition: string | null; root: string | null };
  error_type?:      string;
  message?:         string;
}

export const explainWord = (word: string, verse?: string, is_followup = false) =>
  post<TreasuresResponse>("/api/treasures/explain", { word, verse, is_followup });


// ── مزاج اليوم ────────────────────────────────────────────────

export interface PoemEntry {
  verse: string; poet: string; explanation: string;
}

export interface MoodResponse {
  response_type: "poems" | "clarify" | "redirect" | "confirm";
  // poems
  feeling_detected?:     string;
  feeling_intensity?:    string;
  category_used?:        string;
  opening_line?:         string;
  poems?:                PoemEntry[];
  closing_line?:         string;
  // clarify / redirect / confirm
  message?:              string;
  suggested_categories?: string[];
  detected_theme?:       string;
  category_guess?:       string;
}

export interface MoodHistoryItem {
  role:    "user" | "assistant";
  content: string;
}

export const getMoodPoems = (user_input: string, history: MoodHistoryItem[] = []) =>
  post<MoodResponse>("/api/mood/poems", { user_input, history });

// ── رحلة عبر الزمن ─────────────────────────────────────────────

export interface JourneyEraPoem {
  era_key: string;
  era_label: string;
  poem_id?: string | null;
  poem_title?: string | null;
  poet_name?: string | null;
  poem_meter?: string | null;
  poem_theme?: string | null;
  verses: string[];
  cinematic_note: string;
  fallback_used: boolean;
}

export interface JourneySummary {
  similarities: string[];
  core_difference: string;
  final_line: string;
}

export interface JourneyResponse {
  status: "ok";
  selected_theme: string;
  intro_line: string;
  eras: JourneyEraPoem[];
  summary: JourneySummary;
  warnings: string[];
}

export const getTimeJourney = (theme: string) =>
  post<JourneyResponse>("/api/journey/explore", { theme });

export interface JourneyTTSResponse {
  success: boolean;
  audio_base64: string;
  mime_type: string;
}

export const getJourneyTTS = (text: string) =>
  post<JourneyTTSResponse>("/api/journey/tts", { text });

// ── ساعدني أكتب (التوليد فقط) ─────────────────────────────────

export interface GenerateVerseRequest {
  idea: string;
  meter_num: number;
  num_verses?: number;
}

export interface GenerateVerseResponse {
  success: boolean;
  meter?: string;
  meter_num?: number;
  verses?: string[];
  message?: string;
}

export const generateVerse = (payload: GenerateVerseRequest) =>
  post<GenerateVerseResponse>("/api/write/generate", payload);

export interface CompleteVerseResponse {
  success: boolean;
  found?: boolean;
  poem_verses?: Array<{ verse_index?: number; verse: string; is_input_match?: boolean }>;
  meta?: {
    poet?: string;
    meter?: string;
    era?: string;
    similarity?: number;
  };
  alternatives?: Array<{
    rank: number;
    poem_verses: Array<{ verse_index?: number; verse: string; is_input_match?: boolean }>;
    meta?: {
      poet?: string;
      meter?: string;
      era?: string;
      similarity?: number;
    };
    matched_verse?: string;
    source?: "database" | "web";
    source_label?: string;
  }>;
  current_index?: number;
  total_candidates?: number;
  message?: string;
}

export const completeVerse = (partial_verse: string) =>
  post<CompleteVerseResponse>("/api/write/complete", { partial_verse });

// ── فسرها لي ───────────────────────────────────────────────────

export interface InterpretMeter {
  arabic: string;
  english: string;
  confidence: number;
}

export interface InterpretEra {
  label: string;
  classical_prob: number;
  modern_prob: number;
}

export interface InterpretTopicTopItem {
  label: string;
  prob: number;
}

export interface InterpretTopic {
  label: string;
  confidence: number;
  top3: InterpretTopicTopItem[];
}

export interface InterpretVerseBreakdown {
  verse: string;
  meaning: string;
}

export interface InterpretData {
  meter: InterpretMeter;
  era: InterpretEra;
  topic: InterpretTopic;
  depth: string;
  summary: string;
  explanation: string;
  verses_breakdown: InterpretVerseBreakdown[];
  imagery: string;
  meter_effect: string;
  key_word: string;
  mood: string;
}

export interface InterpretResponse {
  success: boolean;
  data?: InterpretData;          // أصبحت optional لأن الفشل ما يرجع data
  error_type?: string;
  message?: string;
}

export const interpretVerses = (poem: string, depth: "brief" | "deep" = "brief") =>
  post<InterpretResponse>("/api/interpret/verses", { poem, depth });

export interface InterpretStreamHandlers {
  onClassify?: (data: {
    meter: InterpretMeter;
    era: InterpretEra;
    topic: InterpretTopic;
  }) => void;
  onChunk?: (chunk: string) => void;
  onDone?: (data: InterpretData) => void;
  onError?: (errorType: string, message: string) => void;
}
 
export async function interpretVersesStream(
  poem: string,
  depth: "brief" | "deep",
  handlers: InterpretStreamHandlers,
): Promise<void> {
  const res = await fetch(`${BASE}/api/interpret/verses/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ poem, depth }),
  });
 
  if (!res.ok || !res.body) {
    handlers.onError?.("network_error", `خطأ ${res.status}`);
    return;
  }
 
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
 
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
 
    buffer += decoder.decode(value, { stream: true });
 
    // SSE events مفصولة بـ "\n\n"
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? ""; // آخر جزء قد يكون ناقص
 
    for (const evt of events) {
      if (!evt.trim()) continue;
 
      const lines = evt.split("\n");
      let eventType = "message";
      let dataStr = "";
 
      for (const line of lines) {
        if (line.startsWith("event: ")) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          dataStr = line.slice(6);
        }
      }
 
      if (!dataStr) continue;
 
      try {
        const data = JSON.parse(dataStr);
 
        switch (eventType) {
          case "classify":
            handlers.onClassify?.(data);
            break;
          case "chunk":
            handlers.onChunk?.(data);
            break;
          case "done":
            handlers.onDone?.(data);
            break;
          case "error":
            handlers.onError?.(data.error_type ?? "unknown", data.message ?? "خطأ");
            break;
          case "ping":
            // keep-alive — تجاهل
            break;
        }
      } catch {
        // تجاهل الأحداث المعطوبة
      }
    }
  }
}
// TODO:
// export const generateVerse   = (idea: string)   => post("/api/write/generate",   { idea });




// // =============================================================
// // src/services/api.ts
// // =============================================================

// const BASE = (import.meta.env.VITE_API_URL as string) || "http://localhost:8000";

// export class APIError extends Error {
//   constructor(public status: number, message: string) { super(message); }
// }

// async function post<T>(path: string, body: unknown): Promise<T> {
//   const res = await fetch(`${BASE}${path}`, {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify(body),
//   });
//   if (!res.ok) {
//     const err = await res.json().catch(() => ({}));
//     throw new APIError(res.status, err.detail ?? `خطأ ${res.status}`);
//   }
//   return res.json();
// }

// // ── كنوز الكلمات ──────────────────────────────────────────────

// export interface MeaningEntry {
//   title:       string;
//   explanation: string;
//   source:      "siwar" | "gpt";   // ← من وين المعنى
// }

// export interface ExampleVerse {
//   verse:  string;
//   poet:   string;
//   source: "database" | "gpt";     // ← من وين البيت
// }

// export interface TreasuresResponse {
//   status:          "ok" | "error";
//   // ok
//   word?:            string;
//   plural?:          string;        // ← جمع الكلمة
//   primary_meaning?: string;
//   meanings?:        MeaningEntry[];
//   poetic_usage?:    string;
//   symbolism?:       string;
//   example_verses?:  ExampleVerse[];
//   simple_tip?:      string;
//   confidence?:      "high" | "medium" | "low";
//   siwar?:           { found: boolean; definition: string | null; root: string | null };
//   // error
//   error_type?:      string;
//   message?:         string;
// }

// export const explainWord = (word: string, verse?: string, is_followup = false) =>
//   post<TreasuresResponse>("/api/treasures/explain", { word, verse, is_followup });


// // ── مزاج اليوم ────────────────────────────────────────────────

// export interface PoemEntry {
//   verse: string; poet: string; explanation: string;
// }

// export interface MoodResponse {
//   feeling_detected: string; feeling_intensity: string;
//   category_used: string; opening_line: string;
//   poems: PoemEntry[]; closing_line: string;
// }

// export const getMoodPoems = (user_input: string) =>
//   post<MoodResponse>("/api/mood/poems", { user_input });

// // TODO:
// // export const generateVerse   = (idea: string)   => post("/api/write/generate",   { idea });
// // export const getTimeJourney  = (topic: string)  => post("/api/journey/explore",  { topic });
// // export const interpretVerses = (verses: string) => post("/api/interpret/verses", { verses });
