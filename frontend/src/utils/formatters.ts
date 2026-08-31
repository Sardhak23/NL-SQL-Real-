/**
 * Formatting utilities for numbers, currencies, dates, and SQL syntax
 */

export function formatCurrency(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '$0.00';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return String(value);

  if (Math.abs(num) >= 1_000_000_000) {
    return `$${(num / 1_000_000_000).toFixed(2)}B`;
  }
  if (Math.abs(num) >= 1_000_000) {
    return `$${(num / 1_000_000).toFixed(2)}M`;
  }
  if (Math.abs(num) >= 10_000) {
    return `$${(num / 1_000).toFixed(1)}k`;
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

export function formatNumber(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '0';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return String(value);

  if (Math.abs(num) >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(num) >= 10_000) {
    return `${(num / 1_000).toFixed(1)}k`;
  }

  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 2,
  }).format(num);
}

export function formatPercentage(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '0.0%';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return String(value);
  return `${num.toFixed(1)}%`;
}

export function formatDate(dateString: string): string {
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(d);
  } catch {
    return dateString;
  }
}

export function formatCellContent(value: any, columnName?: string): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'boolean') return value ? 'TRUE' : 'FALSE';
  if (typeof value === 'number') {
    const colLower = (columnName || '').toLowerCase();
    if (
      colLower.includes('price') ||
      colLower.includes('amount') ||
      colLower.includes('revenue') ||
      colLower.includes('spend') ||
      colLower.includes('margin') ||
      colLower.includes('cost') ||
      colLower.includes('discount')
    ) {
      return formatCurrency(value);
    }
    if (colLower.includes('rate') || colLower.includes('pct') || colLower.includes('percentage')) {
      return formatPercentage(value);
    }
    return formatNumber(value);
  }
  return String(value);
}
