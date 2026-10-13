export type Project = { id: number; name: string; color: string; archived: boolean };

export type Entry = {
  id: number;
  title: string;
  notes: string;
  project_id: number | null;
  project_name: string | null;
  project_color: string | null;
  started_at: string;
  ended_at: string | null;
  minutes: number;
  running: boolean;
};

export type EntryInput = {
  title: string;
  notes: string;
  project_id: number | null;
  started_at: string;
  ended_at: string | null;
};

export type Stats = {
  now: string;
  today_minutes: number;
  week_minutes: number;
  month_minutes: number;
  month_days_worked: number;
  by_project: { name: string; color: string; minutes: number }[];
  trend: { date: string; minutes: number }[];
};

export type ReportMonth = {
  month: string;
  entries: number;
  archived: { generated_at: string; size: number } | null;
};

export type Me = { username: string; owner_name: string };

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

// Fired when the server says the session is gone, so the app can show login.
export const UNAUTHORIZED_EVENT = "worklog:unauthorized";

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method,
    credentials: "same-origin",
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401 && !path.startsWith("/api/auth/")) {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  }
  if (!res.ok) {
    let message = res.statusText;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") message = data.detail;
      else if (Array.isArray(data.detail))
        message = data.detail.map((d: { msg: string }) => d.msg.replace(/^Value error, /, "")).join("; ");
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, message);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

export const api = {
  login: (username: string, password: string) => request<Me>("POST", "/api/auth/login", { username, password }),
  logout: () => request<void>("POST", "/api/auth/logout"),
  me: () => request<Me>("GET", "/api/auth/me"),

  projects: () => request<Project[]>("GET", "/api/projects"),
  createProject: (p: Omit<Project, "id">) => request<Project>("POST", "/api/projects", p),
  updateProject: (id: number, p: Omit<Project, "id">) => request<Project>("PUT", `/api/projects/${id}`, p),
  deleteProject: (id: number) => request<void>("DELETE", `/api/projects/${id}`),

  entries: (month: string, filters: { project_id?: string; q?: string } = {}) => {
    const qs = new URLSearchParams({ month });
    if (filters.project_id) qs.set("project_id", filters.project_id);
    if (filters.q) qs.set("q", filters.q);
    return request<Entry[]>("GET", `/api/entries?${qs}`);
  },
  createEntry: (e: EntryInput) => request<Entry>("POST", "/api/entries", e),
  updateEntry: (id: number, e: EntryInput) => request<Entry>("PUT", `/api/entries/${id}`, e),
  deleteEntry: (id: number) => request<void>("DELETE", `/api/entries/${id}`),

  timer: () => request<{ entry: Entry | null; now: string }>("GET", "/api/timer"),
  startTimer: (t: { title: string; notes: string; project_id: number | null }) =>
    request<Entry>("POST", "/api/timer/start", t),
  stopTimer: () => request<Entry>("POST", "/api/timer/stop"),

  stats: () => request<Stats>("GET", "/api/stats"),
  reports: () => request<ReportMonth[]>("GET", "/api/reports"),
  archiveReport: (month: string) => request<{ file: string }>("POST", `/api/reports/${month}/archive`),
};
