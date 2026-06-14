import type { ReactNode } from "react";

type KpiCardProps = {
  label: string;
  value: string;
  detail: string;
  icon: ReactNode;
  tone?: "neutral" | "positive" | "warning" | "danger";
  loading?: boolean;
};

export function KpiCard({
  label,
  value,
  detail,
  icon,
  tone = "neutral",
  loading = false,
}: KpiCardProps) {
  return (
    <article className={`kpi-card kpi-card--${tone}`}>
      <div className="kpi-card__top">
        <span className="kpi-card__label">{label}</span>
        <span className="kpi-card__icon">{icon}</span>
      </div>
      {loading ? (
        <span className="skeleton skeleton--value" />
      ) : (
        <strong className="kpi-card__value">{value}</strong>
      )}
      <span className="kpi-card__detail">{detail}</span>
    </article>
  );
}
