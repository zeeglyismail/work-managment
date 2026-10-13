import { FormEvent, useEffect, useState } from "react";
import { api, Entry, EntryInput, Project } from "../api";
import { toInputValue } from "../format";
import ProjectSelect from "./ProjectSelect";

type Props = {
  entry: Entry | null; // null = new entry
  projects: Project[];
  onClose: () => void;
  onSaved: () => void;
};

function initial(entry: Entry | null): EntryInput {
  if (entry) {
    return {
      title: entry.title,
      notes: entry.notes,
      project_id: entry.project_id,
      started_at: entry.started_at.slice(0, 16),
      ended_at: entry.ended_at ? entry.ended_at.slice(0, 16) : null,
    };
  }
  const end = new Date();
  const start = new Date(end.getTime() - 60 * 60 * 1000);
  return { title: "", notes: "", project_id: null, started_at: toInputValue(start), ended_at: toInputValue(end) };
}

export default function EntryModal({ entry, projects, onClose, onSaved }: Props) {
  const [form, setForm] = useState<EntryInput>(() => initial(entry));
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const set = <K extends keyof EntryInput>(k: K, v: EntryInput[K]) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (entry) await api.updateEntry(entry.id, form);
      else await api.createEntry(form);
      onSaved();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <form className="card modal" onSubmit={submit}>
        <h2>{entry ? "Edit entry" : "Add entry"}</h2>
        <label>
          What did you work on?
          <input value={form.title} onChange={(e) => set("title", e.target.value)} maxLength={200} autoFocus required />
        </label>
        <label>
          Project
          <ProjectSelect projects={projects} value={form.project_id} onChange={(v) => set("project_id", v)} />
        </label>
        <div className="row2">
          <label>
            Start
            <input type="datetime-local" value={form.started_at} onChange={(e) => set("started_at", e.target.value)} required />
          </label>
          <label>
            End
            <input
              type="datetime-local"
              value={form.ended_at ?? ""}
              onChange={(e) => set("ended_at", e.target.value || null)}
            />
          </label>
        </div>
        {form.ended_at === null && <p className="hint">No end time — this entry will be the running timer.</p>}
        <label>
          <span>
            Notes <span className="muted">(optional)</span>
          </span>
          <textarea rows={3} value={form.notes} onChange={(e) => set("notes", e.target.value)} maxLength={5000} />
        </label>
        {error && <p className="error">{error}</p>}
        <div className="actions">
          <button type="button" className="ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="primary" disabled={busy}>
            {busy ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </div>
  );
}
