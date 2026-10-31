import { onMounted, onBeforeUnmount } from 'vue'

/** Call fn every `ms` while the tab is visible (no websockets on PythonAnywhere). */
export function usePoll(fn, ms) {
  let timer = null
  const tick = async () => {
    if (document.visibilityState === 'visible') {
      try { await fn() } catch { /* ignore transient errors */ }
    }
    timer = setTimeout(tick, ms)
  }
  const onVis = () => document.visibilityState === 'visible' && fn().catch(() => {})
  onMounted(() => {
    timer = setTimeout(tick, ms)
    document.addEventListener('visibilitychange', onVis)
  })
  onBeforeUnmount(() => {
    clearTimeout(timer)
    document.removeEventListener('visibilitychange', onVis)
  })
}
