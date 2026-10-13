import { Project } from "../api";

type Props = {
  projects: Project[];
  value: number | null;
  onChange: (id: number | null) => void;
  id?: string;
};

export default function ProjectSelect({ projects, value, onChange, id }: Props) {
  // Archived projects stay selectable only for entries that already use them.
  const options = projects.filter((p) => !p.archived || p.id === value);
  return (
    <select id={id} value={value ?? ""} onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}>
      <option value="">No project</option>
      {options.map((p) => (
        <option key={p.id} value={p.id}>
          {p.name}
        </option>
      ))}
    </select>
  );
}
