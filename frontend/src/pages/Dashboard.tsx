import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, Entry, Project, Stats } from "../api";
import EntryList from "../components/EntryList";
import EntryModal from "../components/EntryModal";
import ProjectSelect from "../components/ProjectSelect";
import { fmtClock, fmtDay, fmtMinutes, parseLocal } from "../format";

function useTicker(active: boolean) {
  const [, setTick] = useState(0);
  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, [active]);
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [today, setToday] = useState<Entry[]>([]);
  const [running, setRunning] = useState<Entry | null>(null);
  // Seconds the timer had already run when fetched, and when we fetched it.
  const [base, setBase] = useState({ seconds: 0, at: Date.now() });
  const [title, setTitle] = useState("");
  const [projectId, setProjectId] = useState<number | null>(null);
  const [editing, setEditing] = useState<Entry | null | "new">(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [s, p, t] = await Promise.all([api.stats(), api.projects(), api.timer()]);
      const todayKey = s.now.slice(0, 10);
      const month = await api.entries(todayKey.slice(0, 7));
      setStats(s);
      setProjects(p);
      setRunning(t.entry);
      if (t.entry) {
        const secs = (parseLocal(t.now).getTime() - parseLocal(t.entry.started_at).getTime()) / 1000;
        setBase({ seconds: secs, at: Date.now() });
      }
      setToday(month.filter((e) => e.started_at.startsWith(todayKey)));
      setError("");
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    load();
    // Keep totals fresh if the tab stays open all day.
    const id = setInterval(load, 60_000);
    return () => clearInterval(id);
  }, [load]);

  useTicker(!!running);

  const start = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api.startTimer({ title, notes: "", project_id: projectId });
      setTitle("");
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const stop = async () => {
    try {
      await api.stopTimer();
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const remove = async (e: Entry) => {
    if (!confirm(`Delete "${e.title}"?`)) return;
    await api.deleteEntry(e.id).catch((err) => setError(err.message));
    load();
  };

  const elapsed = base.seconds + (Date.now() - base.at) / 1000;
  const trendMax = Math.max(60, ...(stats?.trend.map((d) => d.minutes) ?? [0]));
  const monthTotal = stats?.month_minutes || 1;

  return (
    <div className="page">
      <div className="page-head">
        <h1>{stats ? fmtDay(stats.now) : "Today"}</h1>
        <button className="ghost" onClick={() => setEditing("new")}>
          + Add past entry
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <section className={running ? "card timer live" : "card timer"}>
        {running ? (
          <>
            <div className="timer-info">
              <span className="pulse" aria-hidden />
              <div>
                <div className="label">Working on</div>
                <div className="timer-title">{running.title}</div>
                <div className="muted">{running.project_name ?? "No project"}</div>
              </div>
            </div>
            <div className="clock" aria-live="off">
              {fmtClock(elapsed)}
            </div>
            <button className="danger-solid" onClick={stop}>
              Stop
            </button>
          </>
        ) : (
          <form className="timer-form" onSubmit={start}>
            <input
              placeholder="What are you working on?"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={200}
              required
              aria-label="What are you working on?"
            />
            <ProjectSelect projects={projects} value={projectId} onChange={setProjectId} />
            <button className="primary">Start</button>
          </form>
        )}
      </section>

      {stats && (
        <div className="kpis">
          <div className="card kpi">
            <div className="kpi-val">{fmtMinutes(stats.today_minutes)}</div>
            <div className="kpi-lbl">Today</div>
          </div>
          <div className="card kpi">
            <div className="kpi-val">{fmtMinutes(stats.week_minutes)}</div>
            <div className="kpi-lbl">This week</div>
          </div>
          <div className="card kpi">
            <div className="kpi-val">{fmtMinutes(stats.month_minutes)}</div>
            <div className="kpi-lbl">This month</div>
          </div>
          <div className="card kpi">
            <div className="kpi-val">{stats.month_days_worked}</div>
            <div className="kpi-lbl">Days worked this month</div>
          </div>
        </div>
      )}

      <div className="grid2">
        <section className="card">
          <h2>Today's log</h2>
          <EntryList
            entries={today}
            onEdit={setEditing}
            onDelete={remove}
            empty="Nothing logged today. Start the timer above when you begin."
          />
        </section>

        {stats && (
          <div className="stack">
            <section className="card">
              <h2>Last 14 days</h2>
              <div className="bars" role="img" aria-label="Hours worked per day over the last 14 days">
                {stats.trend.map((d) => (
                  <div key={d.date} className="bar-col" title={`${fmtDay(d.date)}: ${fmtMinutes(d.minutes)}`}>
                    <div className="bar" style={{ height: `${(d.minutes / trendMax) * 100}%` }} />
                    <span>{parseLocal(d.date).getDate()}</span>
                  </div>
                ))}
              </div>
            </section>
            <section className="card">
              <h2>This month by project</h2>
              {stats.by_project.length ? (
                <ul className="split">
                  {stats.by_project.map((p) => (
                    <li key={p.name}>
                      <div className="split-head">
                        <span>{p.name}</span>
                        <span className="muted">{fmtMinutes(p.minutes)}</span>
                      </div>
                      <div className="meter">
                        <div style={{ width: `${(p.minutes / monthTotal) * 100}%`, background: p.color }} />
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty">No time logged this month yet.</p>
              )}
            </section>
          </div>
        )}
      </div>

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
