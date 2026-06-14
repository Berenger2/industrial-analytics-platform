import { useMemo, useState } from "react";
import { Layout } from "./components/Layout";
import { useCubeQuery } from "./hooks/useCubeQuery";
import { DashboardPage } from "./pages/DashboardPage";
import { ProductionPage } from "./pages/ProductionPage";
import { QualityPage } from "./pages/QualityPage";
import type { DashboardFilters, PageId } from "./types/cube";

function defaultFilters(): DashboardFilters {
  const year = new Date().getFullYear();
  return {
    site: "",
    startDate: `${year}-01-01`,
    endDate: `${year}-12-31`,
  };
}

export function App() {
  const [activePage, setActivePage] = useState<PageId>("dashboard");
  const [filters, setFilters] = useState<DashboardFilters>(defaultFilters);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const sitesQuery = useCubeQuery({
    dimensions: ["Sites.site"],
    order: { "Sites.site": "asc" },
  });
  const sites = useMemo(
    () =>
      sitesQuery.data
        .map((row) => row["Sites.site"])
        .filter((site): site is string => Boolean(site)),
    [sitesQuery.data],
  );

  const commonProps = {
    filters,
    sites,
    sitesLoading: sitesQuery.loading,
    onFiltersChange: setFilters,
  };

  return (
    <Layout
      activePage={activePage}
      onNavigate={setActivePage}
      onToggleSidebar={() => setSidebarOpen((open) => !open)}
      sidebarOpen={sidebarOpen}
    >
      {activePage === "dashboard" && <DashboardPage {...commonProps} />}
      {activePage === "production" && <ProductionPage {...commonProps} />}
      {activePage === "quality" && <QualityPage {...commonProps} />}
    </Layout>
  );
}
