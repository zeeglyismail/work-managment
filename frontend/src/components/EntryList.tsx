import type { CSSProperties } from "react";
import { Entry } from "../api";
import { fmtDay, fmtMinutes, fmtTime } from "../format";

type Props = {
  entries: Entry[];
  onEdit: (e: Entry) => void;
  onDelete: (e: Entry) => void;
  groupByDay?: boolean;
  empty?: string;
};

function Row({ e, onEdit, onDelete }: { e: Entry; onEdit: Props["onEdit"]; onDelete: Props["onDelete"] }) {
  return (
    <li className={e.running ? "entry running" : "entry"}>
      <div className="when">
        {fmtTime(e.started_at)}–{e.ended_at ? fmtTime(e.ended_at) : "now"}
      </div>
      <div className="what">
        <div className="title">{e.title}</div>
        <div className="meta">
          <span className="tag" style={{ "--c": e.project_color ?? "#9ca3af" } as CSSProperties}>
            {e.project_name ?? "No project"}
          </span>
          {e.notes && <span className="notes">{e.notes}</span>}
        </div>
      </div>
      <div className="dur">{e.running ? "running" : fmtMinutes(e.minutes)}</div>
      <div className="row-actions">
        <button className="ghost small" onClick={() => onEdit(e)} aria-label={`Edit ${e.title}`}>
          Edit
        </button>
        <button className="ghost small danger" onClick={() => onDelete(e)} aria-label={`Delete ${e.title}`}>
          Delete
        </button>
      </div>
    </li>
  );
}

export default function EntryList({ entries, onEdit, onDelete, groupByDay, empty = "Nothing logged yet." }: Props) {
  if (!entries.length) return <p className="empty">{empty}</p>;

  if (!groupByDay) {
    return (
      <ul className="entries">
        {entries.map((e) => (
          <Row key={e.id} e={e} onEdit={onEdit} onDelete={onDelete} />
        ))}
      </ul>
    );
  }

  const days = new Map<string, Entry[]>();
  for (const e of entries) {
    const d = e.started_at.slice(0, 10);
    days.set(d, [...(days.get(d) ?? []), e]);
  }
  return (
    <div className="days">
      {[...days.entries()].map(([day, items]) => (
        <section key={day} className="day">
          <h3>
            <span>{fmtDay(day)}</span>
            <span className="muted">{fmtMinutes(items.reduce((s, e) => s + e.minutes, 0))}</span>
          </h3>
          <ul className="entries">
            {items.map((e) => (
              <Row key={e.id} e={e} onEdit={onEdit} onDelete={onDelete} />
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
