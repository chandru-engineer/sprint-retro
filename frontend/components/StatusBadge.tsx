const LABELS: Record<string, string> = {
  draft: "Draft",
  open: "Open",
  completed: "Completed",
  submitted: "Submitted",
  pending: "Pending",
  not_started: "Not Started",
  sent: "Sent",
  failed: "Failed",
};

export default function StatusBadge({ status }: { status: string }) {
  const cls =
    {
      draft: "badge-draft",
      open: "badge-open",
      completed: "badge-completed",
      submitted: "badge-submitted",
      pending: "badge-pending",
      not_started: "badge-draft",
      sent: "badge-open",
      failed: "badge-pending",
    }[status] || "badge-draft";

  return <span className={`badge ${cls}`}>{LABELS[status] || status}</span>;
}
