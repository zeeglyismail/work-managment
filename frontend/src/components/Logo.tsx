export default function Logo() {
  return (
    <svg className="logo" viewBox="0 0 24 24" aria-hidden>
      <rect width="24" height="24" rx="6" fill="var(--accent)" />
      <circle cx="12" cy="12" r="6.5" fill="none" stroke="var(--accent-ink)" strokeWidth="2" />
      <path d="M12 8.5V12l2.5 1.5" fill="none" stroke="var(--accent-ink)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
