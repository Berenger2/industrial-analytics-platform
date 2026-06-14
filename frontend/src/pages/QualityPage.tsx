import { useMemo } from "react";
import { FilterBar } from "../components/FilterBar";
import { AlertIcon, ShieldIcon, TrendIcon } from "../components/icons";
import { KpiCard } from "../components/KpiCard";
import { PageHeader } from "../components/PageHeader";
import { SectionCard } from "../components/SectionCard";
import { StatePanel } from "../components/StatePanel";
import { useCubeQuery } from "../hooks/useCubeQuery";
import type { DashboardFilters } from "../types/cube";
import { formatCompact, formatPercent, toNumber } from "../utils/format";
import { buildFilters } from "../utils/queries";

type QualityPageProps = {
  filters: DashboardFilters;
  sites: string[];
  sitesLoading: boolean;
  onFiltersChange: (filters: DashboardFilters) => void;
};

export function QualityPage({
  filters,
  sites,
  sitesLoading,
  onFiltersChange,
}: QualityPageProps) {
  const queryFilters = useMemo(
    () => buildFilters(filters, "QualityControls.month"),
    [filters],
  );
  const bySite = useCubeQuery({
    measures: [
      "QualityControls.qualityControlCount",
      "QualityControls.nonConformityCount",
    ],
    dimensions: ["Sites.site"],
    filters: queryFilters,
    order: { "QualityControls.nonConformityCount": "desc" },
  });
  const byStatus = useCubeQuery({
    measures: ["QualityControls.qualityControlCount"],
    dimensions: ["QualityControls.status"],
    filters: queryFilters,
    order: { "QualityControls.qualityControlCount": "desc" },
  });

  const controls = bySite.data.reduce(
    (sum, row) =>
      sum + toNumber(row["QualityControls.qualityControlCount"]),
    0,
  );
  const nonConformities = bySite.data.reduce(
    (sum, row) =>
      sum + toNumber(row["QualityControls.nonConformityCount"]),
    0,
  );
  const conformityRate = controls
    ? ((controls - nonConformities) / controls) * 100
    : 0;

  return (
    <>
      <PageHeader
        description="Analysez les contrôles, les non-conformités et leur répartition par site."
        eyebrow="Assurance qualité"
        title="Qualité"
      />
      <FilterBar
        filters={filters}
        loadingSites={sitesLoading}
        onChange={onFiltersChange}
        sites={sites}
      />
      {(bySite.error ?? byStatus.error) && (
        <StatePanel
          message={bySite.error ?? byStatus.error ?? ""}
          title="Données qualité indisponibles"
          type="error"
        />
      )}

      <section className="kpi-grid kpi-grid--three">
        <KpiCard
          detail="Échantillons inspectés"
          icon={<ShieldIcon />}
          label="Contrôles qualité"
          loading={bySite.loading}
          value={formatCompact(controls)}
        />
        <KpiCard
          detail="Contrôles avec défaut détecté"
          icon={<AlertIcon />}
          label="Non-conformités"
          loading={bySite.loading}
          tone="danger"
          value={formatCompact(nonConformities)}
        />
        <KpiCard
          detail="Contrôles sans non-conformité"
          icon={<TrendIcon />}
          label="Taux de conformité"
          loading={bySite.loading}
          tone="positive"
          value={formatPercent(conformityRate)}
        />
      </section>

      <div className="quality-grid">
        <SectionCard
          subtitle="Contrôles et écarts détectés"
          title="Qualité par site"
        >
          <div className="quality-list">
            {bySite.loading &&
              Array.from({ length: 3 }, (_, index) => (
                <span className="skeleton skeleton--quality" key={index} />
              ))}
            {!bySite.loading &&
              bySite.data.map((row) => {
                const siteControls = toNumber(
                  row["QualityControls.qualityControlCount"],
                );
                const siteIssues = toNumber(
                  row["QualityControls.nonConformityCount"],
                );
                const ratio = siteControls
                  ? (siteIssues / siteControls) * 100
                  : 0;
                return (
                  <article className="quality-row" key={row["Sites.site"]}>
                    <div>
                      <strong>{row["Sites.site"]}</strong>
                      <span>{siteControls} contrôle(s)</span>
                    </div>
                    <div className="quality-row__bar">
                      <span style={{ width: `${Math.min(ratio, 100)}%` }} />
                    </div>
                    <strong className={siteIssues ? "text-danger" : "text-success"}>
                      {siteIssues} NC
                    </strong>
                  </article>
                );
              })}
          </div>
        </SectionCard>

        <SectionCard
          subtitle="Résultat des inspections"
          title="Répartition des statuts"
        >
          <div className="status-distribution">
            {byStatus.loading &&
              Array.from({ length: 3 }, (_, index) => (
                <span className="skeleton skeleton--status" key={index} />
              ))}
            {!byStatus.loading &&
              byStatus.data.map((row) => {
                const status = row["QualityControls.status"] ?? "unknown";
                const count = toNumber(
                  row["QualityControls.qualityControlCount"],
                );
                return (
                  <div className="status-distribution__row" key={status}>
                    <span className={`status-badge status-badge--${status}`}>
                      {status}
                    </span>
                    <div>
                      <span
                        style={{
                          width: `${controls ? (count / controls) * 100 : 0}%`,
                        }}
                      />
                    </div>
                    <strong>{count}</strong>
                  </div>
                );
              })}
          </div>
        </SectionCard>
      </div>
    </>
  );
}
