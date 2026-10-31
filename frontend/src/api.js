// Tiny fetch wrapper with JWT auth + automatic token refresh.
const BASE = import.meta.env.VITE_API_BASE || '/api'
const ACCESS = 'cb_access'
const REFRESH = 'cb_refresh'

export const tokens = {
  get access() { return localStorage.getItem(ACCESS) },
  get refresh() { return localStorage.getItem(REFRESH) },
  set({ access, refresh }) {
    if (access) localStorage.setItem(ACCESS, access)
    if (refresh) localStorage.setItem(REFRESH, refresh)
  },
  clear() { localStorage.removeItem(ACCESS); localStorage.removeItem(REFRESH) },
}

export class ApiError extends Error {
  constructor(status, data) {
    super(firstError(data) || `Request failed (${status})`)
    this.status = status
    this.data = data || {}
  }
}

function firstError(data) {
  if (!data) return ''
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  for (const [k, v] of Object.entries(data)) {
    const msg = Array.isArray(v) ? v[0] : v
    if (typeof msg === 'string') return k === 'non_field_errors' ? msg : `${k.replace(/_/g, ' ')}: ${msg}`
    if (msg && typeof msg === 'object') return firstError(msg)
  }
  return ''
}

let refreshing = null
async function refreshAccess() {
  if (!tokens.refresh) return false
  refreshing ||= fetch(`${BASE}/auth/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: tokens.refresh }),
  })
    .then(async (r) => {
      if (!r.ok) return false
      tokens.set(await r.json())
      return true
    })
    .catch(() => false)
    .finally(() => setTimeout(() => (refreshing = null), 0))
  return refreshing
}

export const authEvents = new EventTarget()

async function request(method, path, body, retry = true) {
  const headers = { Accept: 'application/json' }
  let payload
  if (body instanceof FormData) payload = body
  else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  if (tokens.access) headers.Authorization = `Bearer ${tokens.access}`
  const res = await fetch(BASE + path, { method, headers, body: payload })
  if (res.status === 401 && retry && tokens.access) {
    if (await refreshAccess()) return request(method, path, body, false)
    tokens.clear()
    authEvents.dispatchEvent(new Event('logout'))
    return request(method, path, body, false)
  }
  if (res.status === 204) return null
  const isJson = res.headers.get('content-type')?.includes('application/json')
  const data = isJson ? await res.json() : await res.text()
  if (!res.ok) throw new ApiError(res.status, data)
  return data
}

export const api = {
  get: (p) => request('GET', p),
  post: (p, b = {}) => request('POST', p, b),
  patch: (p, b) => request('PATCH', p, b),
  del: (p) => request('DELETE', p),
}

/** Build a FormData from an object, skipping undefined/null and encoding booleans. */
export function toForm(obj) {
  const fd = new FormData()
  for (const [k, v] of Object.entries(obj)) {
    if (v === undefined || v === null || v === '') continue
    fd.append(k, typeof v === 'boolean' ? (v ? 'true' : 'false') : v)
  }
  return fd
}
