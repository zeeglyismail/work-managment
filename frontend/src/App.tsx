import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import Logo from "./components/Logo";
import { api, Me, UNAUTHORIZED_EVENT } from "./api";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Entries from "./pages/Entries";
import Projects from "./pages/Projects";
import Reports from "./pages/Reports";

const NAV = [
  { to: "/", label: "Today", end: true },
  { to: "/entries", label: "Log" },
  { to: "/projects", label: "Projects" },
  { to: "/reports", label: "Reports" },
];

export default function App() {
  const [me, setMe] = useState<Me | null | undefined>(undefined);

  useEffect(() => {
    api.me().then(setMe, () => setMe(null));
    const onUnauthorized = () => setMe(null);
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, []);

  if (me === undefined) return <div className="boot" />;
  if (me === null) return <Login onLogin={setMe} />;

  const logout = async () => {
    await api.logout().catch(() => undefined);
    setMe(null);
  };

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <Logo />
          Worklog
        </div>
        <nav>
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end}>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <button className="ghost small" onClick={logout}>
          Sign out
        </button>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/entries" element={<Entries />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
