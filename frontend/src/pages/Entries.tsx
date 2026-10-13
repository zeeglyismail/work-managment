import { useCallback, useEffect, useState } from "react";
import { api, Entry, Project } from "../api";
import EntryList from "../components/EntryList";
import EntryModal from "../components/EntryModal";
import { fmtMinutes, monthKey, monthLabel, shiftMonth } from "../format";

export default function Entries() {
  const [month, setMonth] = useState(() => monthKey(new Date()));
  const [projectFilter, setProjectFilter] = useState("");
  const [q, setQ] = useState("");
  const [query, setQuery] = useState("");
  const [entries, setEntries] = useState<Entry[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [editing, setEditing] = useState<Entry | null | "new">(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setEntries(await api.entries(month, { project_id: projectFilter, q: query }));
      setError("");
    } catch (err) {
      setError((err as Error).message);
    }
  }, [month, projectFilter, query]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    api.projects().then(setProjects, () => undefined);
  }, []);

  // Debounce search so we don't hit the API on every keystroke.
  useEffect(() => {
    const id = setTimeout(() => setQuery(q.trim()), 300);
    return () => clearTimeout(id);
  }, [q]);

  const remove = async (e: Entry) => {
    if (!confirm(`Delete "${e.title}"?`)) return;
    await api.deleteEntry(e.id).catch((err) => setError(err.message));
    load();
  };

  const total = entries.reduce((s, e) => s + e.minutes, 0);

  return (
    <div className="page">
      <div className="page-head">
        <div className="month-nav">
          <button className="ghost small" onClick={() => setMonth((m) => shiftMonth(m, -1))} aria-label="Previous month">
            ‹
          </button>
          <h1>{monthLabel(month)}</h1>
          <button className="ghost small" onClick={() => setMonth((m) => shiftMonth(m, 1))} aria-label="Next month">
            ›
          </button>
        </div>
        <div className="head-actions">
          <a className="button ghost" href={`/api/entries/export.csv?month=${month}`}>
            Export CSV
          </a>
          <button className="primary" onClick={() => setEditing("new")}>
            + Add entry
          </button>
        </div>
      </div>

      <div className="filters">
        <input type="search" placeholder="Search title or notes" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={projectFilter} onChange={(e) => setProjectFilter(e.target.value)} aria-label="Filter by project">
          <option value="">All projects</option>
          <option value="0">No project</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <span className="muted total">
          {entries.length} entries · {fmtMinutes(total)}
        </span>
      </div>

      {error && <p className="error">{error}</p>}

      <section className="card">
        <EntryList entries={entries} onEdit={setEditing} onDelete={remove} groupByDay empty="No entries for this month." />
      </section>

      {editing && (
        <EntryModal
          entry={editing === "new" ? null : editing}
          projects={projects}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
        />
      )}
    </div>
  );
}
