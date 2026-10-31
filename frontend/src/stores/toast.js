import { reactive } from 'vue'

export const toasts = reactive([])
let id = 0

export function toast(message, kind = 'ok', ms = 3200) {
  const t = { id: ++id, message, kind }
  toasts.push(t)
  setTimeout(() => toasts.splice(toasts.indexOf(t), 1), ms)
}
export const toastError = (e) => toast(e?.message || 'Something went wrong', 'error', 4500)
