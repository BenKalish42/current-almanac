/**
 * Task 12.5 — Global Date Formatting
 *
 * formatDate formats a Date for display based on user preference:
 * US -> MM/DD/YYYY HH:mm
 * EU -> DD/MM/YYYY HH:mm
 * ASIAN -> YYYY/MM/DD HH:mm
 */

export type DateFormatType = "US" | "EU" | "ASIAN";

/**
 * Formats a date for display based on format type.
 */
export function formatDate(date: Date, formatType: DateFormatType | string): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  const h = String(date.getHours()).padStart(2, "0");
  const min = String(date.getMinutes()).padStart(2, "0");
  const timePart = `${h}:${min}`;

  switch (formatType) {
    case "EU":
      return `${d}/${m}/${y} ${timePart}`;
    case "ASIAN":
      return `${y}/${m}/${d} ${timePart}`;
    case "US":
    default:
      return `${m}/${d}/${y} ${timePart}`;
  }
}

/** Time only (HH:mm 24h) — for hour pillar bounds when no date component. */
export function formatTime24(date: Date): string {
  const h = String(date.getHours()).padStart(2, "0");
  const min = String(date.getMinutes()).padStart(2, "0");
  return `${h}:${min}`;
}
