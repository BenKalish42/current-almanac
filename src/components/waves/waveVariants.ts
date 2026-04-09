import type { Component } from "vue";
import WaveGifVeil from "./variants/WaveGifVeil.vue";
import WaveDoubleStrip from "./variants/WaveDoubleStrip.vue";
import WaveBrookIntro from "./variants/WaveBrookIntro.vue";

export type WaveVariantId = "gif_veil" | "double_strip" | "brook_intro";

/** Legacy picker value: migrate to default water style + ripple toggle. */
export const LEGACY_WAVE_VARIANT_FLASH_RIPPLE = "flash_ripple" as const;

export const DEFAULT_WAVE_VARIANT_ID: WaveVariantId = "brook_intro";

export interface WaveVariantDefinition {
  id: WaveVariantId;
  label: string;
  supportsAudio: boolean;
  component: Component;
}

export const WAVE_VARIANTS: WaveVariantDefinition[] = [
  { id: "gif_veil", label: "River veil (GIF-style)", supportsAudio: false, component: WaveGifVeil },
  { id: "double_strip", label: "Double-strip waves", supportsAudio: false, component: WaveDoubleStrip },
  { id: "brook_intro", label: "Brook intro pulse", supportsAudio: true, component: WaveBrookIntro },
];

const byId: Record<WaveVariantId, WaveVariantDefinition> = {
  gif_veil: WAVE_VARIANTS[0]!,
  double_strip: WAVE_VARIANTS[1]!,
  brook_intro: WAVE_VARIANTS[2]!,
};

export function isWaveVariantId(value: string): value is WaveVariantId {
  return value === "gif_veil" || value === "double_strip" || value === "brook_intro";
}

export function getWaveVariantDefinition(id: string | undefined | null): WaveVariantDefinition {
  if (id && isWaveVariantId(id)) return byId[id];
  return byId[DEFAULT_WAVE_VARIANT_ID]!;
}

export function getWaveVariantLabel(id: WaveVariantId): string {
  return byId[id]?.label ?? byId[DEFAULT_WAVE_VARIANT_ID]!.label;
}
