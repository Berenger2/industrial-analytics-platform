const compactNumber = new Intl.NumberFormat("fr-FR", {
  notation: "compact",
  maximumFractionDigits: 1,
});

const integerNumber = new Intl.NumberFormat("fr-FR", {
  maximumFractionDigits: 0,
});

const percentage = new Intl.NumberFormat("fr-FR", {
  maximumFractionDigits: 1,
});

export function toNumber(value: string | null | undefined): number {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function formatCompact(value: number): string {
  return compactNumber.format(value);
}

export function formatInteger(value: number): string {
  return integerNumber.format(value);
}

export function formatPercent(value: number): string {
  return `${percentage.format(value)} %`;
}

export function formatMonth(value: string | null | undefined): string {
  if (!value) {
    return "N/A";
  }
  return new Intl.DateTimeFormat("fr-FR", {
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "N/A";
  }
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}
