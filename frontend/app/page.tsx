"use client";

import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Circle, FolderKanban, ListTodo, LogOut, Plus, RefreshCw, Trash2, Upload, X } from "lucide-react";
import { api, resolveAssetUrl, type DashboardStats, type FileRecord, type Project, type Task } from "../lib/api";
import { useAuth } from "../lib/auth-context";

type Dialog = "project" | "task" | "file" | null;
const STATUS_OPTIONS = ["todo", "in_progress", "done"] as const;
type TaskFilter = "all" | "open" | "completed";

function normalizeStatus(value: string): string {
  const trimmed = value.trim();
  if (trimmed === "To Do" || trimmed === "Todo") return "todo";
  if (trimmed === "In Progress") return "in_progress";
  if (trimmed === "Done") return "done";
  return trimmed || "todo";
}

export default function HomePage() {
  const { user, logout } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dialog, setDialog] = useState<Dialog>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [projectId, setProjectId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [taskFilter, setTaskFilter] = useState<TaskFilter>("all");
  const [filesOpen, setFilesOpen] = useState(false);
  const [fileProjectFilter, setFileProjectFilter] = useState("");
  const projectsSection = useRef<HTMLDivElement>(null);
  const tasksSection = useRef<HTMLDivElement>(null);
  const filesSection = useRef<HTMLElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [projectsResult, tasksResult, statsResult, filesResult] = await Promise.all([
        api.projects(),
        api.tasks(),
        api.dashboardStats(),
        api.files(),
      ]);
      setProjects(projectsResult);
      setTasks(tasksResult);
      setStats(statsResult);
      setFiles(filesResult);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load your workspace.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function closeDialog() {
    setDialog(null);
    setTitle("");
    setDescription("");
    setProjectId("");
    setFile(null);
    if (fileInput.current) fileInput.current.value = "";
  }

  async function createProject(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const created = await api.createProject({ title, description });
      setProjects((current) => [...current, created]);
      closeDialog();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not create project.");
    } finally {
      setBusy(false);
    }
  }

  async function createTask(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      if (!projectId) {
        setError("Choose a project before creating a task.");
        return;
      }
      const created = await api.createTask({
        project_id: Number(projectId),
        title,
        description,
        status: "todo",
        priority: "Medium",
        due_date: null,
      });
      setTasks((current) => [...current, created]);
      closeDialog();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not create task.");
    } finally {
      setBusy(false);
    }
  }

  async function changeStatus(task: Task, status: string) {
    try {
      const updated = await api.updateTask(task.id, { status: normalizeStatus(status) });
      setTasks((current) => current.map((item) => (item.id === task.id ? updated : item)));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not update task.");
    }
  }

  async function upload(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    try {
      const uploaded = await api.uploadFile(file, projectId ? Number(projectId) : undefined);
      setFiles((current) => [uploaded, ...current]);
      closeDialog();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not upload file.");
    } finally {
      setBusy(false);
    }
  }

  async function deleteFileRecord(fileId: number) {
    try {
      await api.deleteFile(fileId);
      setFiles((current) => current.filter((item) => item.id !== fileId));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not delete file.");
    }
  }

  async function deleteTask(taskId: number) {
    try {
      await api.deleteTask(taskId);
      setTasks((current) => current.filter((task) => task.id !== taskId));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not delete task.");
    }
  }

  function showProjects() {
    setTaskFilter("all");
    setFileProjectFilter("");
    projectsSection.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function showTasks(filter: TaskFilter) {
    setTaskFilter(filter);
    tasksSection.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const normalizedTasks = tasks.map((task) => ({ ...task, status: normalizeStatus(task.status) }));
  const openTasks = normalizedTasks.filter((task) => task.status === "todo" || task.status === "in_progress");
  const completed = normalizedTasks.filter((task) => task.status === "done").length;
  const visibleTasks = normalizedTasks.filter((task) => {
    if (taskFilter === "completed") return task.status === "done";
    if (taskFilter === "open") return task.status === "todo" || task.status === "in_progress";
    return true;
  });
  const visibleFiles = files.filter((fileRecord) => !fileProjectFilter || String(fileRecord.project_id ?? "") === fileProjectFilter);

  return (
    <div className="dashboard-shell">
      <section className="dashboard-hero">
        <div>
          <p className="eyebrow">Your command center</p>
          <h1>Make progress visible.</h1>
          <p className="hero-copy">Welcome back, {user?.full_name || user?.username || "there"}. Keep the important work close, clear, and moving forward.</p>
        </div>
        <div className="flex gap-2">
          <button className="icon-button" onClick={() => void load()} disabled={loading} aria-label="Refresh">
            <RefreshCw size={18} className={loading ? "spin" : ""} />
          </button>
          <button onClick={logout} className="icon-button" aria-label="Sign out">
            <LogOut size={18} />
          </button>
        </div>
      </section>

      {error && <p className="error-banner" role="alert">{error}</p>}

      <section className="stats-grid">
        <button type="button" className="stat-card stat-coral text-left" onClick={showProjects}>
          <FolderKanban size={20} />
          <span>Projects</span>
          <strong>{stats?.total_projects ?? projects.length}</strong>
        </button>
        <button type="button" className="stat-card stat-sage text-left" onClick={() => showTasks("open")}>
          <ListTodo size={20} />
          <span>Open tasks</span>
          <strong>{openTasks.length}</strong>
        </button>
        <button type="button" className="stat-card stat-mustard text-left" onClick={() => showTasks("completed")}>
          <CheckCircle2 size={20} />
          <span>Completed</span>
          <strong>{completed}</strong>
        </button>
        <button type="button" className="stat-card stat-ink text-left" onClick={() => setFilesOpen(true)}>
          <Upload size={20} />
          <span>Files</span>
          <strong>{files.length}</strong>
        </button>
      </section>

      <div className="mt-8 flex flex-wrap gap-3">
        <button className="rounded-lg bg-ink px-4 py-3 font-bold text-white" onClick={() => setDialog("project")}>
          <Plus className="mr-2 inline" size={17} />New project
        </button>
        <button className="rounded-lg border border-ink px-4 py-3 font-bold text-ink" onClick={() => setDialog("task")}>
          <Plus className="mr-2 inline" size={17} />New task
        </button>
        <button className="rounded-lg border border-ink px-4 py-3 font-bold text-ink" onClick={() => setDialog("file")}>
          <Upload className="mr-2 inline" size={17} />Upload file
        </button>
      </div>

      <section className="workspace-grid">
        <div className="panel" ref={projectsSection}>
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Overview</p>
              <h2>Projects</h2>
            </div>
            <span>{projects.length} total</span>
          </div>
          {loading ? (
            <p className="muted">Loading projects...</p>
          ) : projects.length === 0 ? (
            <p className="muted">No projects yet.</p>
          ) : (
            <div className="project-list">
              {projects.slice(0, 8).map((project) => (
                <article key={project.id}>
                  <div className="project-mark" />
                  <div>
                    <h3>{project.title}</h3>
                    <p>{project.description || "No description added"}</p>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>

        <div className="panel" ref={tasksSection}>
          <div className="panel-heading">
            <div>
              <p className="eyebrow">In motion</p>
              <h2>Tasks</h2>
            </div>
            <span>{taskFilter === "all" ? `${openTasks.length} active` : taskFilter === "open" ? "Open tasks" : "Completed tasks"}</span>
          </div>
          {loading ? (
            <p className="muted">Loading tasks...</p>
          ) : visibleTasks.length === 0 ? (
            <p className="muted">No tasks yet.</p>
          ) : (
            <div className="task-list">
              {visibleTasks.slice(0, 10).map((task) => (
                <div className="task-row" key={task.id}>
                  {task.status === "done" ? <CheckCircle2 size={17} /> : <Circle size={17} />}
                  <div>
                    <strong>{task.title}</strong>
                    <span>{task.priority} priority</span>
                  </div>
                  <select
                    aria-label={`Status for ${task.title}`}
                    value={task.status}
                    onChange={(e) => void changeStatus(task, e.target.value)}
                    className="rounded border border-slate-200 bg-transparent px-2 py-1 text-xs"
                  >
                    {STATUS_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option === "in_progress" ? "In progress" : option === "todo" ? "To do" : "Done"}
                      </option>
                    ))}
                  </select>
                  <button type="button" onClick={() => void deleteTask(task.id)} aria-label={`Delete ${task.title}`} className="icon-button text-red-600">
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="panel mt-8">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Files</p>
            <h2>Uploads</h2>
          </div>
          <span>{files.length} total</span>
        </div>

        <select value={fileProjectFilter} onChange={(event) => setFileProjectFilter(event.target.value)} className="mb-4 rounded border border-slate-200 bg-transparent px-3 py-2 text-sm" aria-label="Filter files by project">
          <option value="">All projects</option>
          {projects.map((project) => <option key={project.id} value={project.id}>{project.title}</option>)}
        </select>

        {loading ? (
          <p className="muted">Loading files...</p>
        ) : visibleFiles.length === 0 ? (
          <p className="muted">No files uploaded yet.</p>
        ) : (
          <div className="project-list">
            {visibleFiles.map((fileRecord) => {
              const fileUrl = resolveAssetUrl(fileRecord.file_url);
              const isImage = /\.(png|jpe?g|gif|webp|svg|bmp)$/i.test(fileRecord.filename);
              const projectName = projects.find((project) => project.id === fileRecord.project_id)?.title;

              return (
                <article key={fileRecord.id}>
                  {isImage && <img src={fileUrl} alt={fileRecord.filename} className="h-16 w-16 rounded-lg object-cover" />}
                  <div className="flex-1">
                    <h3>{fileRecord.filename}</h3>
                    <p>
                      {fileRecord.file_type || "File"} · {fileRecord.file_size} bytes
                    </p>
                    <small className="font-bold text-ink">{projectName ? `Linked to: ${projectName}` : "Not linked to a project"}</small>
                  </div>
                  <div className="flex gap-2">
                    <a href={fileUrl} target="_blank" rel="noreferrer" className="rounded border border-ink px-2 py-1 text-xs font-bold text-ink">
                      Open
                    </a>
                    <button type="button" onClick={() => void deleteFileRecord(fileRecord.id)} className="rounded border border-red-500 px-2 py-1 text-xs font-bold text-red-600">
                      Delete
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      {filesOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-ink/50 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-3xl rounded-2xl bg-white p-6 shadow-soft">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="font-display text-2xl font-bold text-ink">Uploaded files</h2>
              <button onClick={() => setFilesOpen(false)} aria-label="Close uploaded files"><X /></button>
            </div>
            <div className="project-list">
              {visibleFiles.length === 0 ? <p className="muted">No files match this project.</p> : visibleFiles.map((fileRecord) => {
                const fileUrl = resolveAssetUrl(fileRecord.file_url);
                const projectName = projects.find((project) => project.id === fileRecord.project_id)?.title;
                return <article key={fileRecord.id}><div className="flex-1"><h3>{fileRecord.filename}</h3><p>{projectName ? `Linked to: ${projectName}` : "Not linked to a project"}</p></div><a href={fileUrl} target="_blank" rel="noreferrer" className="rounded border border-ink px-2 py-1 text-xs font-bold text-ink">Open</a></article>;
              })}
            </div>
          </div>
        </div>
      )}

      {dialog && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-ink/50 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-soft">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="font-display text-2xl font-bold text-ink">
                {dialog === "project" ? "New project" : dialog === "task" ? "New task" : "Upload file"}
              </h2>
              <button onClick={closeDialog} aria-label="Close">
                <X />
              </button>
            </div>

            {dialog === "file" ? (
              <form onSubmit={upload}>
                <input
                  ref={fileInput}
                  required
                  type="file"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="mb-4 w-full rounded-lg border border-slate-200 p-3"
                />
                <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className="mb-5 w-full rounded-lg border border-slate-200 p-3">
                  <option value="">No project</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.title}
                    </option>
                  ))}
                </select>
                <button disabled={busy || !file} className="w-full rounded-lg bg-ink p-3 font-bold text-white disabled:opacity-50">
                  {busy ? "Uploading..." : "Upload file"}
                </button>
              </form>
            ) : (
              <form onSubmit={dialog === "project" ? createProject : createTask}>
                <input
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder={dialog === "project" ? "Project title" : "Task title"}
                  className="mb-3 w-full rounded-lg border border-slate-200 p-3"
                />
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Description (optional)"
                  className="mb-3 min-h-24 w-full rounded-lg border border-slate-200 p-3"
                />
                {dialog === "task" && (
                  <select required value={projectId} onChange={(e) => setProjectId(e.target.value)} className="mb-5 w-full rounded-lg border border-slate-200 p-3">
                    <option value="">Choose a project</option>
                    {projects.map((project) => (
                      <option key={project.id} value={project.id}>
                        {project.title}
                      </option>
                    ))}
                  </select>
                )}
                <button disabled={busy} className="w-full rounded-lg bg-ink p-3 font-bold text-white disabled:opacity-50">
                  {busy ? "Saving..." : dialog === "project" ? "Create project" : "Create task"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
