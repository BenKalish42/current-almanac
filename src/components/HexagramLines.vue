<script setup lang="ts">
const props = defineProps<{
  binary: string | null; // 6 chars, TOP→BOTTOM, "1"/"0"
  size?: "sm" | "md";
}>();

const h = props.size === "sm" ? 6 : 10;
const lineGap = props.size === "sm" ? 2 : 4;
const w = props.size === "sm" ? 44 : 62;
const seg = Math.round(w * 0.42);
</script>

<template>
  <div v-if="binary" class="hex" :style="{ gap: lineGap + 'px' }">
    <div v-for="(ch, idx) in binary.split('')" :key="idx" class="line">
      <!-- yang -->
      <div v-if="ch === '1'" class="solid" :style="{ height: h + 'px', width: w + 'px' }" />
      <!-- yin -->
      <div v-else class="broken" :style="{ height: h + 'px', width: w + 'px', gap: seg + 'px' }">
        <div class="seg" :style="{ height: h + 'px', width: seg + 'px' }" />
        <div class="seg" :style="{ height: h + 'px', width: seg + 'px' }" />
      </div>
    </div>
  </div>
  <div v-else class="dash">—</div>
</template>

<style scoped>
.hex {
  display: grid;
  margin-top: 8px;
  justify-items: center;
}
.line {
  display: flex;
  justify-content: center;
}
.solid {
  background: rgba(255, 255, 255, 1);
  border-radius: 2px;
}
.broken {
  display: flex;
  align-items: center;
  justify-content: center;
}
.seg {
  background: rgba(255, 255, 255, 1);
  border-radius: 2px;
}
.dash {
  color: rgba(0, 0, 0, 0.5);
  margin-top: 6px;
}
</style>