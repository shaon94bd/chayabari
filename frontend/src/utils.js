export const taka = (n) => (n == null ? '' : '৳' + Number(n).toLocaleString('en-IN'))

export function dateShort(d) {
  return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}
export function dateTime(d) {
  return new Date(d).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}
export function timeAgo(d) {
  const s = (Date.now() - new Date(d)) / 1000
  if (s < 60) return 'now'
  if (s < 3600) return `${Math.floor(s / 60)}m`
  if (s < 86400) return `${Math.floor(s / 3600)}h`
  if (s < 604800) return `${Math.floor(s / 86400)}d`
  return dateShort(d)
}
/** Value for <input type="datetime-local"> from a Date. */
export function toLocalInput(d) {
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
}
export const fromLocalInput = (v) => (v ? new Date(v).toISOString() : null)

export const saleLabel = {
  not_for_sale: 'Not for sale',
  available: 'For sale',
  reserved: 'Reserved',
  sold: 'Sold',
}

export async function share({ title, text, url }) {
  url ||= location.href
  if (navigator.share) {
    try { await navigator.share({ title, text, url }); return 'shared' } catch { return null }
  }
  await navigator.clipboard?.writeText(url)
  return 'copied'
}
