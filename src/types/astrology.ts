/**
 * Master TypeScript interfaces for the San Shi (Three Styles) astrological systems.
 * Guides frontend props and shared data structures across QMDJ, Da Liu Ren, Tai Yi.
 */

export type SanShiSystem = "qmdj" | "daliuren" | "taiyi";

export interface WeatherBadge {
  id: string;
  type: "auspicious" | "inauspicious" | "neutral";
  label: string;
  description: string;
}

export interface QMDJPalace {
  index: number;
  name: string;
  direction: string;
  heavenStem: string;
  earthStem: string;
  star: string;
  door: string;
  spirit: string;
}

export interface DaLiuRenEarthCell {
  branch: string;
  heavenPan: string;
  index: number;
}

export interface DaLiuRenData {
  siKe: string[];
  sanChuan: string[];
  earthBoard: DaLiuRenEarthCell[];
}

export interface TaiYiData {
  accumulationYear: number;
  year: number;
  configurationNumber: number;
  palaceIndex: number;
  palaceNumber: number;
  dun: "Yang" | "Yin";
}
