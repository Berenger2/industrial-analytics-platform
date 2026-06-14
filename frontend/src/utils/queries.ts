import type { CubeFilter, DashboardFilters } from "../types/cube";

export function buildFilters(
  filters: DashboardFilters,
  timeMember: string,
): CubeFilter[] {
  const result: CubeFilter[] = [
    {
      member: timeMember,
      operator: "inDateRange",
      values: [filters.startDate, filters.endDate],
    },
  ];

  if (filters.site) {
    result.push({
      member: "Sites.site",
      operator: "equals",
      values: [filters.site],
    });
  }

  return result;
}
