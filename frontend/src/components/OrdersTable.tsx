import type { CubeRow } from "../types/cube";
import { formatInteger, formatMonth, toNumber } from "../utils/format";
import { StatePanel } from "./StatePanel";

type OrdersTableProps = {
  rows: CubeRow[];
  loading?: boolean;
};

const statusLabels: Record<string, string> = {
  planned: "Planifié",
  in_progress: "En cours",
  completed: "Terminé",
  cancelled: "Annulé",
};

export function OrdersTable({ rows, loading = false }: OrdersTableProps) {
  if (loading) {
    return (
      <div className="table-loading">
        {Array.from({ length: 5 }, (_, index) => (
          <span className="skeleton skeleton--row" key={index} />
        ))}
      </div>
    );
  }

  if (!rows.length) {
    return (
      <StatePanel
        message="Modifiez le site ou la période pour élargir la recherche."
        title="Aucun ordre de fabrication"
      />
    );
  }

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Ordre</th>
            <th>Site</th>
            <th>Produit</th>
            <th>Mois</th>
            <th>Statut</th>
            <th className="numeric">Planifié</th>
            <th className="numeric">Produit</th>
            <th className="numeric">Rebut</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const status = row["ProductionOrders.status"] ?? "unknown";
            return (
              <tr key={row["ProductionOrders.orderNumber"]}>
                <td className="order-number">
                  {row["ProductionOrders.orderNumber"]}
                </td>
                <td>{row["Sites.site"]}</td>
                <td>{row["Products.product"]}</td>
                <td>{formatMonth(row["ProductionOrders.month"])}</td>
                <td>
                  <span className={`status-badge status-badge--${status}`}>
                    {statusLabels[status] ?? status}
                  </span>
                </td>
                <td className="numeric">
                  {formatInteger(
                    toNumber(row["ProductionOrders.plannedQuantity"]),
                  )}
                </td>
                <td className="numeric">
                  {formatInteger(
                    toNumber(row["ProductionOrders.producedQuantity"]),
                  )}
                </td>
                <td className="numeric">
                  {formatInteger(
                    toNumber(row["ProductionOrders.scrapQuantity"]),
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
