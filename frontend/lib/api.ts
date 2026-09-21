export type Project = { id: number; user_id: number; title: string; description: string | null };
export type Task = { id: number; project_id: number; title: string; description: string | null; status: string; priority: string; due_date: string | null };
export type TeamMember = { id: number; user_id: number; name: string; email: string; role: string; color: string; presence: string };
export type FileRecord = { id: number; user_id: number; filename: string; file_size: string; file_type: string; file_url: string; project_id: number | null; upload_date: string };
export type ActivityLog = { id: number; user_id: number; action: string; details: string | null; timestamp: string };
export type DashboardStats = { total_projects: number; total_tasks: number; tasks_by_status: Record<string, number>; tasks_by_priority: Record<string, number>; team_members: number; completion_rate: number };
export type LoginResponse = { access_token: string; token_type: string };
export type User = { id: number; username: string; email?: string | null; full_name?: string | null };
export type SearchEntry = { id: number; title: string; status?: string };
export type SearchResponse = { query: string; results: { projects: SearchEntry[]; tasks: SearchEntry[] } };

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export function resolveAssetUrl(path: string): string {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.name = "ApiError"; this.status = status; }
}

function getToken(): string | null {
  return typeof window === "undefined" ? null : localStorage.getItem("access_token");
}

async function request<T>(path: string, init: RequestInit = {}, includeAuth = true): Promise<T> {
  const headers = new Headers(init.headers);
  const token = includeAuth ? getToken() : null;
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (
    init.body &&
    !(init.body instanceof FormData) &&
    !(init.body instanceof URLSearchParams) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    let message = "Request failed";
    try {
      const body = (await response.json()) as { detail?: string | Array<{ msg?: string }> };
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail)) {
        message = body.detail.map((item) => item.msg || "Invalid request").join(", ");
      }
    } catch {
      message = response.statusText || message;
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  login(username: string, password: string) {
    return request<LoginResponse>(
      "/auth/login",
      {
        method: "POST",
        body: new URLSearchParams({ username, password }),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      },
      false,
    );
  },
  me: () => request<User>("/auth/me"),
  projects: () => request<Project[]>("/projects"),
  createProject: (data: { title: string; description?: string }) => request<Project>("/projects", { method: "POST", body: JSON.stringify(data) }),
  updateProject: (id: number, data: Partial<Pick<Project, "title" | "description">>) => request<Project>(`/projects/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteProject: (id: number) => request<void>(`/projects/${id}`, { method: "DELETE" }),
  tasks: (projectId?: number, status?: string) => { const params = new URLSearchParams(); if (projectId !== undefined) params.set("project_id", String(projectId)); if (status) params.set("status", status); return request<Task[]>(`/tasks${params.toString() ? `?${params}` : ""}`); },
  createTask: (data: Omit<Task, "id">) => request<Task>("/tasks", { method: "POST", body: JSON.stringify(data) }),
  updateTask: (id: number, data: Partial<Omit<Task, "id" | "project_id">>) => request<Task>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteTask: (id: number) => request<void>(`/tasks/${id}`, { method: "DELETE" }),
  team: () => request<TeamMember[]>("/team"),
  addTeamMember: (data: Omit<TeamMember, "id" | "user_id">) => request<TeamMember>("/team", { method: "POST", body: JSON.stringify(data) }),
  updateTeamMember: (id: number, data: Partial<Omit<TeamMember, "id" | "user_id">>) => request<TeamMember>(`/team/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteTeamMember: (id: number) => request<void>(`/team/${id}`, { method: "DELETE" }),
  files: (projectId?: number) => request<FileRecord[]>(projectId === undefined ? "/files" : `/files?project_id=${projectId}`),
  uploadFile: (file: File, projectId?: number) => {
    const formData = new FormData();
    formData.append("file", file);
    if (projectId !== undefined) formData.append("project_id", String(projectId));
    return request<FileRecord>("/files/upload", { method: "POST", body: formData });
  },
  deleteFile: (id: number) => request<void>(`/files/${id}`, { method: "DELETE" }),
  activity: (limit = 50) => request<ActivityLog[]>(`/activity?limit=${limit}`),
  dashboardStats: () => request<DashboardStats>("/dashboard/stats"),
  search: (query: string) => request<SearchResponse>(`/search?q=${encodeURIComponent(query)}`),
};
