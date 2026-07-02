export type HealthStatus = {
  status: string;
  service: string;
  version: string;
};

export type DbHealthStatus = {
  status: string;
  database: string;
  checked_at: string;
  tables: string[];
};

export type TeamMember = {
  id: number;
  name: string;
  email: string | null;
  department: string | null;
  position: string | null;
  phone: string | null;
  role: string;
  is_active: number;
  created_at: string;
  updated_at: string;
};

export type TeamMemberInput = {
  name: string;
  email?: string;
  department?: string;
  position?: string;
  phone?: string;
  role?: string;
};

export type Schedule = {
  id: number;
  owner_id: number;
  owner_name: string | null;
  type: string;
  title: string;
  description: string | null;
  location: string | null;
  start_at: string;
  end_at: string;
  visibility: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ScheduleInput = {
  owner_id: number;
  type: string;
  title: string;
  description?: string;
  location?: string;
  start_at: string;
  end_at: string;
};

export type NewsArticle = {
  id: number;
  title: string;
  source: string;
  url: string;
  published_at: string | null;
  summary: string | null;
  category: string | null;
  collected_at: string;
};

export type NewsCollectionRun = {
  id: number;
  target_date: string;
  mode: string;
  status: string;
  fetched_count: number;
  inserted_count: number;
  duplicate_count: number;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
};

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  adminPin?: string;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (options.adminPin) {
    headers["X-Admin-Pin"] = options.adminPin;
  }

  const response = await fetch(path, {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = (await response.json()) as { message?: string };
      message = payload.message ?? message;
    } catch {
      // Keep the HTTP status message when the server did not return JSON.
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthStatus>("/api/health"),
  dbHealth: () => request<DbHealthStatus>("/api/db/health"),
  teamMembers: () => request<{ items: TeamMember[] }>("/api/team-members"),
  createTeamMember: (input: TeamMemberInput, adminPin: string) =>
    request<{ item: TeamMember }>("/api/team-members", { method: "POST", body: input, adminPin }),
  updateTeamMember: (id: number, input: TeamMemberInput, adminPin: string) =>
    request<{ item: TeamMember }>(`/api/team-members/${id}`, { method: "PATCH", body: input, adminPin }),
  deleteTeamMember: (id: number, adminPin: string) =>
    request<{ status: string }>(`/api/team-members/${id}`, { method: "DELETE", adminPin }),
  schedules: (from: string, to: string) =>
    request<{ items: Schedule[] }>(`/api/schedules?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`),
  createSchedule: (input: ScheduleInput, adminPin: string) =>
    request<{ item: Schedule }>("/api/schedules", { method: "POST", body: input, adminPin }),
  updateSchedule: (id: number, input: ScheduleInput, adminPin: string) =>
    request<{ item: Schedule }>(`/api/schedules/${id}`, { method: "PATCH", body: input, adminPin }),
  deleteSchedule: (id: number, adminPin: string) =>
    request<{ status: string }>(`/api/schedules/${id}`, { method: "DELETE", adminPin }),
  newsArticles: (date?: string) =>
    request<{ items: NewsArticle[] }>(`/api/news/articles${date ? `?date=${encodeURIComponent(date)}` : ""}`),
  newsRuns: (limit = 20) =>
    request<{ items: NewsCollectionRun[] }>(`/api/news/runs?limit=${encodeURIComponent(String(limit))}`),
  collectNews: (targetDate: string, adminPin: string) =>
    request<{
      run_id: number;
      target_date: string;
      mode: string;
      status: string;
      fetched_count: number;
      inserted_count: number;
      duplicate_count: number;
    }>("/api/news/collect", { method: "POST", body: { target_date: targetDate }, adminPin }),
};
