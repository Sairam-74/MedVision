import { format, formatDistanceToNowStrict } from 'date-fns';

export function formatDateTime(value: string) {
  return format(new Date(value), 'MMM d, yyyy · HH:mm');
}

export function formatRelative(value: string) {
  return formatDistanceToNowStrict(new Date(value), { addSuffix: true });
}

export function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}
