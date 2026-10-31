<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import { toastError } from '@/stores/toast'
import { usePoll } from '@/composables/usePoll'
import { dateTime } from '@/utils'
import TopBar from '@/components/TopBar.vue'
import Icon from '@/components/Icon.vue'

const route = useRoute()
const auth = useAuth()
const id = route.params.id
const conv = ref(null)
const msgs = ref([])
const body = ref('')
const sending = ref(false)
const scroller = ref(null)
const hasOlder = ref(true)
const artworkRef = ref(route.query.artwork ? +route.query.artwork : null)

const lastId = () => (msgs.value.length ? msgs.value[msgs.value.length - 1].id : 0)
const scrollDown = () => nextTick(() => window.scrollTo(0, document.body.scrollHeight))

onMounted(async () => {
  const [all, m] = await Promise.all([api.get('/conversations/'), api.get(`/conversations/${id}/messages/`)])
  conv.value = all.find((c) => c.id === +id)
  msgs.value = m
  hasOlder.value = m.length >= 50
  scrollDown()
})

async function poll() {
  const fresh = await api.get(`/conversations/${id}/messages/?after=${lastId()}`)
  if (fresh.length) {
    const nearBottom = window.innerHeight + window.scrollY > document.body.scrollHeight - 120
    msgs.value.push(...fresh.filter((f) => !msgs.value.find((m) => m.id === f.id)))
    if (nearBottom) scrollDown()
  }
}
usePoll(poll, 3000)

async function older() {
  const res = await api.get(`/conversations/${id}/messages/?before=${msgs.value[0].id}`)
  msgs.value.unshift(...res)
  hasOlder.value = res.length >= 50
}

async function send() {
  const text = body.value.trim()
  if (!text) return
  sending.value = true
  try {
    const m = await api.post(`/conversations/${id}/messages/`, { body: text, artwork_id: artworkRef.value })
    artworkRef.value = null
    body.value = ''
    if (!msgs.value.find((x) => x.id === m.id)) msgs.value.push(m)
    scrollDown()
  } catch (e) {
    toastError(e)
  } finally {
    sending.value = false
  }
}
const showDate = (i) => i === 0 || new Date(msgs.value[i].created_at) - new Date(msgs.value[i - 1].created_at) > 30 * 60e3
</script>

<template>
  <TopBar :title="conv?.title || 'Chat'">
    <RouterLink v-if="conv?.other?.role !== 'collector' && conv?.other" :to="`/artists/${conv.other.username}`" class="icon-btn" aria-label="Profile"><Icon name="user" /></RouterLink>
  </TopBar>
  <div class="page thread" ref="scroller">
    <button v-if="hasOlder && msgs.length" class="btn sm ghost block" @click="older">Load earlier messages</button>
    <template v-for="(m, i) in msgs" :key="m.id">
      <div v-if="showDate(i)" class="center tiny faint" style="margin: .8rem 0 .3rem">{{ dateTime(m.created_at) }}</div>
      <div class="bubble-row" :class="{ me: m.sender.id === auth.user.id }">
        <div class="bubble">
          <div v-if="conv?.kind === 'group' && m.sender.id !== auth.user.id" class="tiny" style="font-weight: 600; color: var(--accent)">{{ m.sender.name }}</div>
          <RouterLink v-if="m.artwork" :to="`/artworks/${m.artwork.id}`" class="art-ref">
            <img :src="m.artwork.image" alt="" /><span class="small ellipsis">{{ m.artwork.title }}</span>
          </RouterLink>
          <div style="white-space: pre-wrap; word-break: break-word">{{ m.body }}</div>
        </div>
      </div>
    </template>
    <p v-if="!msgs.length" class="center small muted section">Say hello 👋</p>
  </div>
  <form class="composer" @submit.prevent="send">
    <div class="composer-inner">
      <div v-if="artworkRef" class="tiny muted" style="padding: 0 .3rem .3rem">About artwork #{{ artworkRef }} <a href="#" @click.prevent="artworkRef = null">✕</a></div>
      <div class="row">
        <textarea class="input grow" v-model="body" rows="1" placeholder="Message…" @keydown.enter.exact.prevent="send" />
        <button class="btn accent" :disabled="sending || !body.trim()" aria-label="Send" style="width: 46px; padding: 0"><Icon name="send" /></button>
      </div>
    </div>
  </form>
</template>

<style scoped>
.thread { padding-bottom: 6rem; }
.bubble-row { display: flex; margin: .2rem 0; }
.bubble-row.me { justify-content: flex-end; }
.bubble { max-width: 80%; background: var(--card); padding: .5rem .75rem; border-radius: 16px 16px 16px 4px; box-shadow: var(--shadow); }
.me .bubble { background: var(--ink); color: #fff; border-radius: 16px 16px 4px 16px; }
.art-ref { display: flex; align-items: center; gap: .4rem; margin-bottom: .3rem; padding: .3rem; border-radius: 10px; background: rgb(127 127 127 / 15%); }
.art-ref img { width: 36px; height: 36px; border-radius: 6px; object-fit: cover; }
.composer { position: fixed; left: 0; right: 0; bottom: 0; background: var(--paper); border-top: 1px solid var(--line); padding: .5rem .75rem calc(.5rem + env(safe-area-inset-bottom)); }
.composer-inner { max-width: 680px; margin: 0 auto; }
.composer textarea { min-height: 46px; height: 46px; padding-top: .7rem; resize: none; }
</style>
