import type { DashboardFilters } from "../types/cube";

type FilterBarProps = {
  filters: DashboardFilters;
  sites: string[];
  loadingSites: boolean;
  onChange: (filters: DashboardFilters) => void;
};

export function FilterBar({
  filters,
  sites,
  loadingSites,
  onChange,
}: FilterBarProps) {
  return (
    <section className="filter-bar" aria-label="Filtres">
      <label>
        <span>Site</span>
        <select
          disabled={loadingSites}
          onChange={(event) =>
            onChange({ ...filters, site: event.target.value })
          }
          value={filters.site}
        >
          <option value="">
            {loadingSites ? "Chargement..." : "Tous les sites"}
          </option>
          {sites.map((site) => (
            <option key={site} value={site}>
              {site}
            </option>
          ))}
        </select>
      </label>

      <div className="filter-bar__period">
        <label>
          <span>Du</span>
          <input
            max={filters.endDate}
            onChange={(event) =>
              onChange({ ...filters, startDate: event.target.value })
            }
            type="date"
            value={filters.startDate}
          />
        </label>
        <span className="filter-bar__separator">→</span>
        <label>
          <span>Au</span>
          <input
            min={filters.startDate}
            onChange={(event) =>
              onChange({ ...filters, endDate: event.target.value })
            }
            type="date"
            value={filters.endDate}
          />
        </label>
      </div>
    </section>
  );
}
