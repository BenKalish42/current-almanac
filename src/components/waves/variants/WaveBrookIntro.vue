<script setup lang="ts">
import { onUnmounted, watch } from "vue";
import { usePrefersReducedMotion } from "@/utils/usePrefersReducedMotion";

const props = withDefaults(
  defineProps<{
    brookAudioOn?: boolean;
  }>(),
  { brookAudioOn: false }
);

const reduced = usePrefersReducedMotion();

let audioCtx: AudioContext | null = null;
let gain: GainNode | null = null;
let source: AudioBufferSourceNode | null = null;
let lfo: OscillatorNode | null = null;
let lfoGain: GainNode | null = null;

function stopBrookAudio() {
  try {
    source?.stop();
  } catch {
    /* already stopped */
  }
  source = null;
  try {
    lfo?.stop();
  } catch {
    /* */
  }
  lfo = null;
  lfoGain = null;
  gain = null;
  if (audioCtx && audioCtx.state !== "closed") {
    void audioCtx.close();
  }
  audioCtx = null;
}

function makeNoiseBuffer(ctx: AudioContext, seconds = 2): AudioBuffer {
  const channels = 1;
  const rate = ctx.sampleRate;
  const frames = Math.floor(rate * seconds);
  const buf = ctx.createBuffer(channels, frames, rate);
  const data = buf.getChannelData(0);
  for (let i = 0; i < frames; i++) {
    data[i] = (Math.random() * 2 - 1) * 0.35;
  }
  return buf;
}

async function startBrookAudio() {
  if (reduced.value) return;
  stopBrookAudio();
  const ctx = new AudioContext();
  audioCtx = ctx;
  await ctx.resume().catch(() => undefined);

  const buffer = makeNoiseBuffer(ctx, 2.2);
  const src = ctx.createBufferSource();
  src.buffer = buffer;
  src.loop = true;

  const filter = ctx.createBiquadFilter();
  filter.type = "lowpass";
  filter.frequency.value = 520;
  filter.Q.value = 0.7;

  gain = ctx.createGain();
  gain.gain.value = 0.06;

  lfo = ctx.createOscillator();
  lfo.type = "sine";
  lfo.frequency.value = 0.35;
  lfoGain = ctx.createGain();
  lfoGain.gain.value = 180;
  lfo.connect(lfoGain);
  lfoGain.connect(filter.frequency);

  src.connect(filter);
  filter.connect(gain);
  gain.connect(ctx.destination);

  src.start();
  lfo.start();
  source = src;
}

watch(
  () => props.brookAudioOn,
  (on) => {
    if (!on) {
      stopBrookAudio();
      return;
    }
    void startBrookAudio();
  },
  { immediate: true }
);

watch(reduced, (r) => {
  if (r) stopBrookAudio();
});

onUnmounted(() => {
  stopBrookAudio();
});
</script>

<template>
  <div class="wave-brook-intro" :class="{ 'wave-brook-intro--static': reduced }">
    <div class="wave-brook-intro__wash" />
    <div class="wave-brook-intro__mist" />
    <div class="wave-brook-intro__pulse" />
    <div class="wave-brook-intro__ring" />
  </div>
</template>

<style scoped>
.wave-brook-intro {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.wave-brook-intro__wash {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(13, 21, 32, 0) 0%,
    rgba(28, 58, 112, 0.26) 45%,
    rgba(36, 78, 138, 0.4) 100%
  );
}

.wave-brook-intro__mist {
  position: absolute;
  inset: 0;
  background: radial-gradient(
    ellipse 125% 95% at 50% 100%,
    rgba(72, 148, 228, 0.52) 0%,
    rgba(42, 98, 168, 0.36) 38%,
    rgba(22, 52, 92, 0.2) 58%,
    transparent 78%
  );
  background-size: 120% 120%;
  background-position: 50% 100%;
}

.wave-brook-intro:not(.wave-brook-intro--static) .wave-brook-intro__mist {
  animation: brookMistDrift 22s ease-in-out infinite alternate;
}

.wave-brook-intro__pulse {
  position: absolute;
  inset: -5%;
  background: radial-gradient(
    circle at 50% 86%,
    rgba(150, 205, 255, 0.42) 0%,
    rgba(72, 138, 210, 0.28) 35%,
    rgba(38, 88, 148, 0.12) 55%,
    transparent 72%
  );
  animation: brookPulse 9s ease-in-out infinite;
  will-change: opacity, transform;
}

.wave-brook-intro__ring {
  position: absolute;
  left: 50%;
  bottom: -8%;
  width: 140%;
  height: 55%;
  transform: translateX(-50%);
  border-radius: 50%;
  border: 1px solid rgba(118, 178, 242, 0.38);
  box-shadow:
    0 0 40px rgba(90, 150, 230, 0.24),
    0 0 80px rgba(50, 100, 185, 0.16);
  animation: brookRing 9s ease-in-out infinite;
  pointer-events: none;
}

.wave-brook-intro--static .wave-brook-intro__mist {
  animation: none;
}

.wave-brook-intro--static .wave-brook-intro__pulse,
.wave-brook-intro--static .wave-brook-intro__ring {
  animation: none;
}

.wave-brook-intro--static .wave-brook-intro__pulse {
  opacity: 0.75;
}

.wave-brook-intro--static .wave-brook-intro__ring {
  opacity: 0.65;
  transform: translateX(-50%) scale(1);
}

@keyframes brookMistDrift {
  0% {
    background-position: 42% 98%;
    opacity: 0.92;
  }
  100% {
    background-position: 58% 102%;
    opacity: 1;
  }
}

@keyframes brookPulse {
  0%,
  100% {
    opacity: 0.5;
    transform: scale(1) translate3d(0, 0, 0);
  }
  50% {
    opacity: 1;
    transform: scale(1.1) translate3d(0, -6px, 0);
  }
}

@keyframes brookRing {
  0%,
  100% {
    opacity: 0.4;
    transform: translateX(-50%) translate3d(0, 0, 0) scale(1);
  }
  50% {
    opacity: 0.95;
    transform: translateX(-50%) translate3d(0, -10px, 0) scale(1.06);
  }
}
</style>
