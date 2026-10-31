<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
const props = defineProps({ to: String, serverTime: String })
// Correct for phone clocks that are off by using the server's time as reference.
const skew = props.serverTime ? Date.now() - new Date(props.serverTime).getTime() : 0
const now = ref(Date.now())
let t
onMounted(() => (t = setInterval(() => (now.value = Date.now()), 1000)))
onBeforeUnmount(() => clearInterval(t))
const text = computed(() => {
  let s = Math.max(0, Math.floor((new Date(props.to) - (now.value - skew)) / 1000))
  if (s === 0) return 'Ended'
  const d = Math.floor(s / 86400); s %= 86400
  const h = Math.floor(s / 3600); s %= 3600
  const m = Math.floor(s / 60); s %= 60
  if (d) return `${d}d ${h}h ${m}m`
  if (h) return `${h}h ${m}m ${s}s`
  return `${m}m ${s}s`
})
</script>

<template><span>{{ text }}</span></template>
