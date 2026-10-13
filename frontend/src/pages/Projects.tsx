import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, Project } from "../api";

const PALETTE = ["#4f46e5", "#0891b2", "#059669", "#ca8a04", "#ea580c", "#dc2626", "#db2777", "#7c3aed"];

type Draft = Omit<Project, "id">;

function ProjectForm({ initial, onSubmit, onCancel, submitLabel }: {
  initial: Draft;
  onSubmit: (d: Draft) => Promise<void>;
  onCancel?: () => void;
  submitLabel: string;
}) {
  const [draft, setDraft] = useState(initial);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await onSubmit(draft);
      if (!onCancel) setDraft({ ...initial, color: PALETTE[Math.floor(Math.random() * PALETTE.length)] });
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="project-form" onSubmit={submit}>
      <input
        type="color"
        value={draft.color}
        onChange={(e) => setDraft({ ...draft, color: e.target.value })}
        aria-label="Project colour"
      />
      <input
        placeholder="Project name"
        value={draft.name}
        onChange={(e) => setDraft({ ...draft, name: e.target.value })}
        maxLength={100}
        required
        aria-label="Project name"
      />
      <button className="primary" disabled={busy}>
        {submitLabel}
      </button>
      {onCancel && (
        <button type="button" className="ghost" onClick={onCancel}>
          Cancel
        </button>
      )}
    </form>
  );
}

export default function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => api.projects().then(setProjects, (err) => setError(err.message)), []);
  useEffect(() => {
    load();
  }, [load]);

  const guard = async (fn: () => Promise<unknown>) => {
    try {
      await fn();
      setError("");
      await load();
    } catch (err) {
      setError((err as Error).message);
      throw err;
    }
  };

  const remove = (p: Project) => {
    if (!confirm(`Delete project "${p.name}"? Its entries are kept and moved to "No project".`)) return;
    guard(() => api.deleteProject(p.id)).catch(() => undefined);
  };

  return (
    <div className="page narrow">
      <div className="page-head">
        <h1>Projects</h1>
      </div>
      <p className="muted">Group your work by client, product or kind of task. Reports break time down by project.</p>

      <section className="card">
        <ProjectForm
          initial={{ name: "", color: PALETTE[0], archived: false }}
          onSubmit={(d) => guard(() => api.createProject(d))}
          submitLabel="Add project"
        />
      </section>

      {error && <p className="error">{error}</p>}

      <section className="card">
        {projects.length === 0 ? (
          <p className="empty">No projects yet. Add one above.</p>
        ) : (
          <ul className="project-list">
            {projects.map((p) =>
              editingId === p.id ? (
                <li key={p.id}>
                  <ProjectForm
                    initial={p}
                    onSubmit={(d) => guard(() => api.updateProject(p.id, d)).then(() => setEditingId(null))}
                    onCancel={() => setEditingId(null)}
                    submitLabel="Save"
                  />
                </li>
              ) : (
                <li key={p.id} className={p.archived ? "archived" : ""}>
                  <span className="swatch" style={{ background: p.color }} />
                  <span className="pname">{p.name}</span>
                  {p.archived && <span className="badge">archived</span>}
                  <div className="row-actions">
                    <button className="ghost small" onClick={() => setEditingId(p.id)}>
                      Edit
                    </button>
                    <button
                      className="ghost small"
                      onClick={() => guard(() => api.updateProject(p.id, { ...p, archived: !p.archived })).catch(() => undefined)}
                    >
                      {p.archived ? "Restore" : "Archive"}
                    </button>
                    <button className="ghost small danger" onClick={() => remove(p)}>
                      Delete
                    </button>
                  </div>
                </li>
              ),
            )}
          </ul>
        )}
      </section>
    </div>
  );
}
