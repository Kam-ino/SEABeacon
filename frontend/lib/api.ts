// Resolve the API base on every fetch (not at module load) so the value is
// chosen in the actual browser context — not the Node prerender context where
// `window` is undefined and we'd otherwise bake `localhost:8000` into the
// shipped bundle.
//
//   - explicit override via NEXT_PUBLIC_API_BASE_URL (when meaningful) → use it
//   - browser at localhost / 127.0.0.1 / 0.0.0.0                       → http://localhost:8000
//   - any other browser origin (Vercel deploy etc., per vercel.json)   → /_/backend
//   - non-browser context (SSR, tests)                                 → http://localhost:8000
const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "0.0.0.0"]);
const LOCAL_HOST_URL = /^https?:\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?\/?$/i;

export function getApiBase(): string {
  const raw = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").trim();
  const onBrowser = typeof window !== "undefined";
  const browserOnLocalhost = onBrowser && LOCAL_HOSTS.has(window.location.hostname);

  if (raw && raw !== "/") {
    // Ignore a localhost-pointing env var when the page itself is on a
    // remote origin (e.g. Vercel imported the value from .env.example).
    // Otherwise fetches from production would try to reach localhost.
    const envIsLocal = LOCAL_HOST_URL.test(raw);
    if (!(envIsLocal && onBrowser && !browserOnLocalhost)) {
      return raw.replace(/\/+$/, "");
    }
  }

  if (onBrowser) {
    if (browserOnLocalhost) return "http://localhost:8000";
    return "/_/backend";
  }
  return "http://localhost:8000";
}

// Join the resolved base with a path, guaranteeing exactly one slash between
// them regardless of how either side ends/begins.
export function url(path: string): string {
  const base = getApiBase().replace(/\/+$/, "");
  const tail = path.startsWith("/") ? path : `/${path}`;
  return `${base}${tail}`;
}

export const MAP_STYLE_URL =
  process.env.NEXT_PUBLIC_MAP_STYLE_URL ?? "https://tiles.openfreemap.org/styles/liberty";

export type Severity = "advisory" | "warning" | "urgent";

export interface TrackPoint {
  timestamp: string;
  lat: number;
  lon: number;
  max_wind_kt: number;
  pressure_mb: number;
  category: number;
}

export interface ImpactZone {
  municipality_id: number;
  municipality_name: string;
  country_code: string;
  lat: number;
  lon: number;
  severity: Severity;
  eta_hours: number;
  confidence: number;
}

export interface AlertPayload {
  id: number;
  scenario_id: number;
  country_code: string;
  municipality_id: number | null;
  severity: Severity;
  issued_at: string;
  title: string;
  body: string;
  language: string;
  lat?: number;
  lon?: number;
  municipality_name?: string;
  eta_hours?: number;
  confidence?: number;
}

export interface SignalPayload {
  id: number;
  timestamp: string;
  lat: number;
  lon: number;
  language: string;
  source_type: string;
  text: string;
  classification: "distress" | "observation" | "noise";
  confidence: number;
}

export interface ScenarioDetail {
  id: number;
  slug: string;
  name: string;
  hazard_type: string;
  start_time: string;
  end_time: string;
  description: string;
  track_points: TrackPoint[];
}

export async function getScenario(slug: string): Promise<ScenarioDetail> {
  const res = await fetch(url(`/scenarios/${slug}`));
  if (!res.ok) throw new Error(`failed to fetch scenario: ${res.status}`);
  return res.json();
}

export async function startScenario(slug: string, speed = 60): Promise<void> {
  const res = await fetch(url(`/scenarios/${slug}/run`), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ speed }),
  });
  if (!res.ok) throw new Error(`failed to start scenario: ${res.status}`);
}

export async function stopScenario(slug: string): Promise<void> {
  const res = await fetch(url(`/scenarios/${slug}/stop`), { method: "POST" });
  if (!res.ok) throw new Error(`failed to stop scenario: ${res.status}`);
}

export interface SeekResponse {
  scenario_slug: string;
  scenario_time: string | null;
  running: boolean;
  speed: number;
  track_so_far: TrackPoint[];
  impact_zones: ImpactZone[];
  alerts: AlertPayload[];
  signals: SignalPayload[];
  current_point: TrackPoint | null;
}

export async function seekScenario(
  slug: string,
  scenarioTime: string,
  opts: { resume?: boolean; speed?: number } = {}
): Promise<SeekResponse> {
  const res = await fetch(url(`/scenarios/${slug}/seek`), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      scenario_time: scenarioTime,
      resume: opts.resume ?? false,
      speed: opts.speed ?? 60,
    }),
  });
  if (!res.ok) throw new Error(`failed to seek: ${res.status}`);
  return res.json();
}
