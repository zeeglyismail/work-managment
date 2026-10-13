// All times from the API are naive local wall-clock strings ("2026-10-07T09:00:00").
// Parse them by hand so the browser's own timezone never shifts them.

export function parseLocal(s: string): Date {
  const [d, t = "00:00:00"] = s.split("T");
  const [y, mo, day] = d.split("-").map(Number);
  const [h, mi, sec = 0] = t.split(":").map(Number);
  return new Date(y, mo - 1, day, h, mi, Math.floor(sec));
}

const pad = (n: number) => String(n).padStart(2, "0");

export function toInputValue(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function monthKey(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}`;
}

export function shiftMonth(month: string, delta: number): string {
  const [y, m] = month.split("-").map(Number);
  return monthKey(new Date(y, m - 1 + delta, 1));
}

export function monthLabel(month: string): string {
  const [y, m] = month.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(undefined, { month: "long", year: "numeric" });
}

export function fmtMinutes(min: number): string {
  const h = Math.floor(min / 60);
  const m = min % 60;
  if (h && m) return `${h}h ${m}m`;
  return h ? `${h}h` : `${m}m`;
}

export function fmtClock(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  return `${pad(Math.floor(s / 3600))}:${pad(Math.floor((s % 3600) / 60))}:${pad(s % 60)}`;
}

export function fmtTime(s: string): string {
  return s.slice(11, 16);
}

export function fmtDay(s: string): string {
  return parseLocal(s).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
}
