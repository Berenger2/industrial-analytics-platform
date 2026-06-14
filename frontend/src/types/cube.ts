export type CubeFilter = {
  member: string;
  operator: "equals" | "inDateRange";
  values: string[];
};

export type CubeTimeDimension = {
  dimension: string;
  granularity?: "month";
  dateRange?: [string, string];
};

export type CubeQuery = {
  measures?: string[];
  dimensions?: string[];
  filters?: CubeFilter[];
  timeDimensions?: CubeTimeDimension[];
  order?: Record<string, "asc" | "desc">;
  limit?: number;
};

export type CubeRow = Record<string, string | null>;

export type CubeResponse = {
  data: CubeRow[];
};

export type DashboardFilters = {
  site: string;
  startDate: string;
  endDate: string;
};

export type PageId = "dashboard" | "production" | "quality";
