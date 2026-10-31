import { defineStore } from 'pinia'
import { api, tokens, authEvents } from '@/api'

export const useAuth = defineStore('auth', {
  state: () => ({ user: null, ready: false }),
  getters: {
    loggedIn: (s) => !!s.user,
    isStudent: (s) => !!s.user?.batch,
    isOwner: (s) => s.user?.role === 'owner',
    batch: (s) => s.user?.batch || null,
    batchActive: (s) => !!s.user?.batch?.is_active,
  },
  actions: {
    async init() {
      authEvents.addEventListener('logout', () => (this.user = null))
      if (tokens.access) {
        try { await this.fetchMe() } catch { tokens.clear() }
      }
      this.ready = true
    },
    async fetchMe() {
      this.user = await api.get('/auth/me/')
      return this.user
    },
    async login(username, password) {
      tokens.set(await api.post('/auth/login/', { username: username.trim(), password }))
      return this.fetchMe()
    },
    async acceptSession({ access, refresh, user }) {
      tokens.set({ access, refresh })
      if (user) this.user = user
      else await this.fetchMe()
    },
    logout() {
      tokens.clear()
      this.user = null
    },
  },
})
