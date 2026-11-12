export function formatUtcToLocal(utcString: string | null | undefined): string {
  if (!utcString) return 'N/A';
  const date = new Date(utcString);
  if (Number.isNaN(date.getTime())) return 'Invalid Date';
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatSafeNumber(value: number | null | undefined, fallback = '—'): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return fallback;
  }
  return value.toLocaleString();
}