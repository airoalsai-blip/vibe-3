type StatusBadgeProps = {
  status: "ok" | "error" | "idle";
  label: string;
};

export function StatusBadge({ status, label }: StatusBadgeProps) {
  return <span className={`status-badge status-badge--${status}`}>{label}</span>;
}
