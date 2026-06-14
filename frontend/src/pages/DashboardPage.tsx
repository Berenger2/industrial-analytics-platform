import { useMemo } from "react";
import { FilterBar } from "../components/FilterBar";
import { AlertIcon, FactoryIcon, ShieldIcon, TrendIcon } from "../components/icons";
import { KpiCard } from "../components/KpiCard";
import { OrdersTable } from "../components/OrdersTable";
import { PageHeader } from "../components/PageHeader";
import {
  ProductionChart,
  type ChartPoint,
} from "../components/ProductionChart";
import { SectionCard } from "../components/SectionCard";
import { StatePanel } from "../components/StatePanel";
import { useCubeQuery } from "../hooks/useCubeQuery";
import type { DashboardFilters } from "../types/cube";
import {
  formatCompact,
  formatMonth,
  formatPercent,
  toNumber,
} from "../utils/format";
import { buildFilters } from "../utils/queries";

type DashboardPageProps = {
  filters: DashboardFilters;
  sites: string[];
  sitesLoading: boolean;
  onFiltersChange: (filters: DashboardFilters) => void;
};

export function DashboardPage({
  filters,
  sites,
  sitesLoading,
  onFiltersChange,
}: DashboardPageProps) {
  const productionFilters = useMemo(
    () => buildFilters(filters, "ProductionOrders.month"),
    [filters],
  );
  const qualityFilters = useMemo(
    () => buildFilters(filters, "QualityControls.month"),
    [filters],
  );

  const kpis = useCubeQuery({
    measures: [
      "ProductionOrders.orderCount",
      "ProductionOrders.plannedQuantity",
      "ProductionOrders.producedQuantity",
      "ProductionOrders.scrapQuantity",
      "ProductionOrders.scrapRate",
      "ProductionOrders.delayedOrders",
    ],
    filters: productionFilters,
  });

  const quality = useCubeQuery({
    measures: [
      "QualityControls.qualityControlCount",
      "QualityControls.nonConformityCount",
    ],
    filters: qualityFilters,
  });

  const monthly = useCubeQuery({
    measures: [
      "ProductionOrders.plannedQuantity",
      "ProductionOrders.producedQuantity",
    ],
    timeDimensions: [
      {
        dimension: "ProductionOrders.month",
        granularity: "month",
      },
    ],
    filters: productionFilters,
    order: { "ProductionOrders.month": "asc" },
  });

  const orders = useCubeQuery({
    measures: [
      "ProductionOrders.plannedQuantity",
      "ProductionOrders.producedQuantity",
      "ProductionOrders.scrapQuantity",
    ],
    dimensions: [
      "ProductionOrders.orderNumber",
      "ProductionOrders.status",
      "ProductionOrders.month",
      "Sites.site",
      "Products.product",
    ],
    filters: productionFilters,
    order: { "ProductionOrders.month": "desc" },
    limit: 50,
  });

  const kpiRow = kpis.data[0] ?? {};
  const qualityRow = quality.data[0] ?? {};
  const chartData: ChartPoint[] = monthly.data.map((row) => ({
    label: formatMonth(row["ProductionOrders.month"]),
    planned: toNumber(row["ProductionOrders.plannedQuantity"]),
    produced: toNumber(row["ProductionOrders.producedQuantity"]),
  }));
  const error = kpis.error ?? quality.error ?? monthly.error ?? orders.error;

  return (
    <>
      <PageHeader
        description="Suivez la production, le rebut et la qualité sur l'ensemble du réseau industriel."
        eyebrow="Centre de pilotage"
        title="Vue globale"
      />
      <FilterBar
        filters={filters}
        loadingSites={sitesLoading}
        onChange={onFiltersChange}
        sites={sites}
      />

      {error && (
        <StatePanel
          message={error}
          title="Impossible de charger les indicateurs"
          type="error"
        />
      )}

      <section className="kpi-grid">
        <KpiCard
          detail="Ordres sur la période"
          icon={<FactoryIcon />}
          label="Ordres de fabrication"
          loading={kpis.loading}
          value={formatCompact(
            toNumber(kpiRow["ProductionOrders.orderCount"]),
          )}
        />
        <KpiCard
          detail="Volume total réalisé"
          icon={<TrendIcon />}
          label="Quantité produite"
          loading={kpis.loading}
          tone="positive"
          value={formatCompact(
            toNumber(kpiRow["ProductionOrders.producedQuantity"]),
          )}
        />
        <KpiCard
          detail={`${formatCompact(
            toNumber(kpiRow["ProductionOrders.scrapQuantity"]),
          )} unités rejetées`}
          icon={<AlertIcon />}
          label="Taux de rebut"
          loading={kpis.loading}
          tone="warning"
          value={formatPercent(
            toNumber(kpiRow["ProductionOrders.scrapRate"]),
          )}
        />
        <KpiCard
          detail={`${formatCompact(
            toNumber(qualityRow["QualityControls.qualityControlCount"]),
          )} contrôles réalisés`}
          icon={<ShieldIcon />}
          label="Non-conformités"
          loading={quality.loading}
          tone="danger"
          value={formatCompact(
            toNumber(qualityRow["QualityControls.nonConformityCount"]),
          )}
        />
      </section>

      <div className="dashboard-grid">
        <SectionCard
          action={
            <div className="chart-legend">
              <span><i className="legend-planned" /> Planifié</span>
              <span><i className="legend-produced" /> Produit</span>
            </div>
          }
          subtitle="Volumes agrégés par mois"
          title="Production mensuelle"
        >
          <ProductionChart data={chartData} loading={monthly.loading} />
        </SectionCard>

        <SectionCard
          subtitle="Respect du plan de production"
          title="Exécution"
        >
          <div className="execution-panel">
            <div className="execution-panel__metric">
              <span>Planifié</span>
              <strong>
                {formatCompact(
                  toNumber(kpiRow["ProductionOrders.plannedQuantity"]),
                )}
              </strong>
            </div>
            <div className="execution-panel__metric">
              <span>Réalisé</span>
              <strong>
                {formatCompact(
                  toNumber(kpiRow["ProductionOrders.producedQuantity"]),
                )}
              </strong>
            </div>
            <div className="progress-track">
              <span
                style={{
                  width: `${Math.min(
                    100,
                    (toNumber(
                      kpiRow["ProductionOrders.producedQuantity"],
                    ) /
                      Math.max(
                        toNumber(
                          kpiRow["ProductionOrders.plannedQuantity"],
                        ),
                        1,
                      )) *
                      100,
                  )}%`,
                }}
              />
            </div>
            <div className="execution-panel__footer">
              <span>Ordres en retard</span>
              <strong>
                {toNumber(kpiRow["ProductionOrders.delayedOrders"])}
              </strong>
            </div>
          </div>
        </SectionCard>
      </div>

      <SectionCard
        subtitle="Derniers ordres correspondant aux filtres"
        title="Ordres de fabrication"
      >
        <OrdersTable loading={orders.loading} rows={orders.data} />
      </SectionCard>
    </>
  );
}
