import { formatCompact } from "../utils/format";

export type ChartPoint = {
  label: string;
  planned: number;
  produced: number;
};

type ProductionChartProps = {
  data: ChartPoint[];
  loading?: boolean;
};

export function ProductionChart({
  data,
  loading = false,
}: ProductionChartProps) {
  if (loading) {
    return <div className="chart-loading skeleton" />;
  }

  if (!data.length) {
    return (
      <div className="chart-empty">
        Aucune production sur la période sélectionnée.
      </div>
    );
  }

  const width = 760;
  const height = 300;
  const padding = { top: 22, right: 16, bottom: 54, left: 55 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const maxValue = Math.max(...data.flatMap((item) => [item.planned, item.produced]), 1);
  const groupWidth = innerWidth / data.length;
  const barWidth = Math.min(30, groupWidth * 0.3);
  const ticks = [0, 0.25, 0.5, 0.75, 1];

  return (
    <div className="chart-wrap">
      <svg
        aria-label="Production mensuelle planifiée et réalisée"
        className="production-chart"
        role="img"
        viewBox={`0 0 ${width} ${height}`}
      >
        {ticks.map((tick) => {
          const y = padding.top + innerHeight * (1 - tick);
          return (
            <g key={tick}>
              <line
                className="chart-grid"
                x1={padding.left}
                x2={width - padding.right}
                y1={y}
                y2={y}
              />
              <text className="chart-axis" x={padding.left - 10} y={y + 4}>
                {formatCompact(maxValue * tick)}
              </text>
            </g>
          );
        })}

        {data.map((point, index) => {
          const center = padding.left + groupWidth * index + groupWidth / 2;
          const plannedHeight = (point.planned / maxValue) * innerHeight;
          const producedHeight = (point.produced / maxValue) * innerHeight;
          return (
            <g key={`${point.label}-${index}`}>
              <rect
                className="chart-bar chart-bar--planned"
                height={plannedHeight}
                rx="3"
                width={barWidth}
                x={center - barWidth - 2}
                y={padding.top + innerHeight - plannedHeight}
              />
              <rect
                className="chart-bar chart-bar--produced"
                height={producedHeight}
                rx="3"
                width={barWidth}
                x={center + 2}
                y={padding.top + innerHeight - producedHeight}
              />
              <text
                className="chart-label"
                textAnchor="middle"
                x={center}
                y={height - 22}
              >
                {point.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
