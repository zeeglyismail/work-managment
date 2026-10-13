import { useCallback, useEffect, useState } from "react";
import { api, ReportMonth } from "../api";
import { monthLabel } from "../format";

export default function Reports() {
  const [months, setMonths] = useState<ReportMonth[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => api.reports().then(setMonths, (err) => setError(err.message)), []);
  useEffect(() => {
    load();
  }, [load]);

  const archive = async (month: string) => {
    setBusy(month);
    try {
      await api.archiveReport(month);
      await load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="page narrow">
      <div className="page-head">
        <h1>Monthly reports</h1>
      </div>
      <p className="muted">
        A PDF for each finished month is saved automatically on the 1st of the next month. You can also download an
        up-to-date PDF of any month at any time.
      </p>

      {error && <p className="error">{error}</p>}

      <section className="card">
        <ul className="report-list">
          {months.map((m) => (
            <li key={m.month}>
              <div>
                <div className="pname">{monthLabel(m.month)}</div>
                <div className="muted small-text">
                  {m.entries} {m.entries === 1 ? "entry" : "entries"}
                  {m.archived && <> · saved copy from {m.archived.generated_at.replace("T", " ").slice(0, 16)}</>}
                </div>
              </div>
              <div className="row-actions">
                <a className="button primary small" href={`/api/reports/${m.month}/pdf`} target="_blank" rel="noreferrer">
                  Download PDF
                </a>
                {m.archived && (
                  <a className="button ghost small" href={`/api/reports/${m.month}/archived`}>
                    Saved copy
                  </a>
                )}
                <button className="ghost small" onClick={() => archive(m.month)} disabled={busy === m.month}>
                  {busy === m.month ? "Saving…" : m.archived ? "Re-save" : "Save copy"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
