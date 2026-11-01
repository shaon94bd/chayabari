// Tiny fetch wrapper with DRF token auth ("Authorization: Token <key>").
const BASE = import.meta.env.VITE_API_BASE || '/api'
const KEY = 'cb_token'

export const tokens = {
  get token() { return localStorage.getItem(KEY) },
  set({ token }) { if (token) localStorage.setItem(KEY, token) },
  clear() { localStorage.removeItem(KEY) },
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

export const authEvents = new EventTarget()

async function request(method, path, body) {
  const headers = { Accept: 'application/json' }
  let payload
  if (body instanceof FormData) payload = body
  else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  if (tokens.token) headers.Authorization = `Token ${tokens.token}`
  const res = await fetch(BASE + path, { method, headers, body: payload })
  if (res.status === 401 && tokens.token) {
    // Token revoked (password changed/reset elsewhere): drop it and retry anonymously.
    tokens.clear()
    authEvents.dispatchEvent(new Event('logout'))
    return request(method, path, body)
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
