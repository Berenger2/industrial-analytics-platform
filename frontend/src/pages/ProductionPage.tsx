import { useMemo } from "react";
import { FilterBar } from "../components/FilterBar";
import { AlertIcon, FactoryIcon, TrendIcon } from "../components/icons";
import { KpiCard } from "../components/KpiCard";
import { OrdersTable } from "../components/OrdersTable";
import { PageHeader } from "../components/PageHeader";
import { SectionCard } from "../components/SectionCard";
import { StatePanel } from "../components/StatePanel";
import { useCubeQuery } from "../hooks/useCubeQuery";
import type { DashboardFilters } from "../types/cube";
import {
  formatCompact,
  formatPercent,
  toNumber,
} from "../utils/format";
import { buildFilters } from "../utils/queries";

type ProductionPageProps = {
  filters: DashboardFilters;
  sites: string[];
  sitesLoading: boolean;
  onFiltersChange: (filters: DashboardFilters) => void;
};

export function ProductionPage({
  filters,
  sites,
  sitesLoading,
  onFiltersChange,
}: ProductionPageProps) {
  const queryFilters = useMemo(
    () => buildFilters(filters, "ProductionOrders.month"),
    [filters],
  );
  const bySite = useCubeQuery({
    measures: [
      "ProductionOrders.orderCount",
      "ProductionOrders.plannedQuantity",
      "ProductionOrders.producedQuantity",
      "ProductionOrders.scrapQuantity",
      "ProductionOrders.scrapRate",
      "ProductionOrders.delayedOrders",
    ],
    dimensions: ["Sites.site"],
    filters: queryFilters,
    order: { "ProductionOrders.producedQuantity": "desc" },
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
    filters: queryFilters,
    order: { "ProductionOrders.month": "desc" },
    limit: 100,
  });

  const totals = bySite.data.reduce(
    (result, row) => ({
      orders: result.orders + toNumber(row["ProductionOrders.orderCount"]),
      planned:
        result.planned + toNumber(row["ProductionOrders.plannedQuantity"]),
      produced:
        result.produced + toNumber(row["ProductionOrders.producedQuantity"]),
      scrap:
        result.scrap + toNumber(row["ProductionOrders.scrapQuantity"]),
      delayed:
        result.delayed + toNumber(row["ProductionOrders.delayedOrders"]),
    }),
    { orders: 0, planned: 0, produced: 0, scrap: 0, delayed: 0 },
  );
  const scrapRate = totals.produced
    ? (totals.scrap / totals.produced) * 100
    : 0;

  return (
    <>
      <PageHeader
        description="Comparez les volumes planifiés et réalisés pour chaque site."
        eyebrow="Performance industrielle"
        title="Production par site"
      />
      <FilterBar
        filters={filters}
        loadingSites={sitesLoading}
        onChange={onFiltersChange}
        sites={sites}
      />
      {bySite.error && (
        <StatePanel
          message={bySite.error}
          title="Données de production indisponibles"
          type="error"
        />
      )}
      <section className="kpi-grid kpi-grid--three">
        <KpiCard
          detail={`${formatCompact(totals.orders)} ordres`}
          icon={<FactoryIcon />}
          label="Production réalisée"
          loading={bySite.loading}
          tone="positive"
          value={formatCompact(totals.produced)}
        />
        <KpiCard
          detail="Objectif de la période"
          icon={<TrendIcon />}
          label="Production planifiée"
          loading={bySite.loading}
          value={formatCompact(totals.planned)}
        />
        <KpiCard
          detail={`${totals.delayed} ordre(s) en retard`}
          icon={<AlertIcon />}
          label="Taux de rebut"
          loading={bySite.loading}
          tone="warning"
          value={formatPercent(scrapRate)}
        />
      </section>

      <SectionCard
        subtitle="Volumes, réalisation et rebut par établissement"
        title="Performance des sites"
      >
        <div className="site-list">
          {bySite.loading &&
            Array.from({ length: 3 }, (_, index) => (
              <span className="skeleton skeleton--site" key={index} />
            ))}
          {!bySite.loading &&
            bySite.data.map((row) => {
              const planned = toNumber(
                row["ProductionOrders.plannedQuantity"],
              );
              const produced = toNumber(
                row["ProductionOrders.producedQuantity"],
              );
              const completion = planned ? (produced / planned) * 100 : 0;
              return (
                <article className="site-row" key={row["Sites.site"]}>
                  <div className="site-row__name">
                    <span className="site-avatar">
                      {(row["Sites.site"] ?? "S").slice(0, 2).toUpperCase()}
                    </span>
                    <div>
                      <strong>{row["Sites.site"]}</strong>
                      <span>
                        {row["ProductionOrders.orderCount"]} ordre(s)
                      </span>
                    </div>
                  </div>
                  <div className="site-row__metric">
                    <span>Produit</span>
                    <strong>{formatCompact(produced)}</strong>
                  </div>
                  <div className="site-row__metric">
                    <span>Rebut</span>
                    <strong>
                      {formatPercent(
                        toNumber(row["ProductionOrders.scrapRate"]),
                      )}
                    </strong>
                  </div>
                  <div className="site-progress">
                    <span>{Math.round(completion)} % du plan</span>
                    <div>
                      <i style={{ width: `${Math.min(completion, 100)}%` }} />
                    </div>
                  </div>
                </article>
              );
            })}
        </div>
      </SectionCard>

      <SectionCard
        subtitle="Détail opérationnel des ordres"
        title="Ordres de fabrication"
      >
        <OrdersTable loading={orders.loading} rows={orders.data} />
      </SectionCard>
    </>
  );
}
