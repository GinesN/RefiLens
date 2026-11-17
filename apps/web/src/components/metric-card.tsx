import { ArrowUpRight } from "lucide-react";
import { Metric, money, multiple } from "@/lib/api";

export default function MetricCard({
  metric,
  onEvidence,
}: {
  metric: Metric;
  onEvidence: (metric: Metric) => void;
}) {
  const meaning: Record<string, string> = {
    gross_debt: "Borrowings on the issuer's stated carrying basis.",
    cash: "Cash and equivalents; availability to the parent can differ.",
    net_debt: "Reported debt after deducting eligible cash.",
    interest_expense:
      "Expense after capitalization; different from cash interest paid.",
  };
  return (
    <button
      className="metric-card"
      onClick={() => onEvidence(metric)}
      aria-label={`Inspect ${metric.label} evidence`}
    >
      <span className="metric-label">
        {metric.label}
        <ArrowUpRight size={15} />
      </span>
      <strong className={metric.value === null ? "unavailable" : ""}>
        {metric.unit === "x" ? multiple(metric.value) : money(metric.value)}
      </strong>
      <span className="metric-basis">{metric.basis}</span>
      {meaning[metric.key] && (
        <span className="metric-meaning">{meaning[metric.key]}</span>
      )}
    </button>
  );
}
