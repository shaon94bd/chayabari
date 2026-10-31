<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import { toast, toastError } from '@/stores/toast'
import { taka, saleLabel, share } from '@/utils'
import TopBar from '@/components/TopBar.vue'
import Avatar from '@/components/Avatar.vue'
import Sheet from '@/components/Sheet.vue'
import Icon from '@/components/Icon.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuth()
const art = ref(null)
const error = ref('')
const active = ref(0)
const buying = ref(false)
const order = reactive({ message: '', contact_phone: auth.user?.phone || '', delivery_address: '' })

const mine = computed(() => auth.user && art.value?.artist.id === auth.user.id)
const images = computed(() => (art.value ? [art.value.image, ...art.value.extra_images.map((i) => i.image)] : []))
const size = computed(() => {
  const a = art.value
  return a?.width_cm && a?.height_cm ? `${+a.width_cm} × ${+a.height_cm} cm` : ''
})

onMounted(async () => {
  try { art.value = await api.get(`/artworks/${route.params.id}/`) } catch (e) { error.value = e.message }
})

function requireLogin() {
  if (!auth.loggedIn) { router.push({ path: '/login', query: { next: route.fullPath } }); return false }
  return true
}
async function placeOrder() {
  try {
    await api.post('/orders/', { artwork_id: art.value.id, ...order })
    buying.value = false
    toast('Request sent! The artist will respond soon.')
    router.push('/orders')
  } catch (e) { toastError(e) }
}
async function message() {
  if (!requireLogin()) return
  try {
    const c = await api.post('/conversations/direct/', { user_id: art.value.artist.id })
    router.push({ path: `/chat/${c.id}`, query: { artwork: art.value.id } })
  } catch (e) { toastError(e) }
}
async function onShare() {
  if ((await share({ title: art.value.title, text: `${art.value.title} by ${art.value.artist.name}` })) === 'copied') toast('Link copied')
}
async function remove() {
  if (!confirm('Delete this artwork permanently?')) return
  try { await api.del(`/artworks/${art.value.id}/`); toast('Deleted'); router.replace('/explore?mine=1') } catch (e) { toastError(e) }
}
</script>

<template>
  <TopBar :title="art?.title || 'Artwork'">
    <button class="icon-btn" aria-label="Share" @click="onShare" v-if="art"><Icon name="share" /></button>
    <RouterLink v-if="mine" :to="`/artworks/${art.id}/edit`" class="icon-btn" aria-label="Edit"><Icon name="edit" /></RouterLink>
  </TopBar>
  <div class="page" v-if="art">
    <div class="hero"><img :src="images[active]" :alt="art.title" /></div>
    <div v-if="images.length > 1" class="thumbs">
      <button v-for="(src, i) in images" :key="src" :class="{ on: i === active }" @click="active = i"><img :src="src" alt="" /></button>
    </div>

    <section class="section stack">
      <div>
        <h1 style="margin-bottom: .2rem">{{ art.title }}</h1>
        <div class="muted">{{ [art.medium, size, art.year].filter(Boolean).join(' · ') }}</div>
      </div>
      <RouterLink :to="`/artists/${art.artist.username}`" class="row">
        <Avatar :user="art.artist" :size="36" />
        <div class="grow"><b>{{ art.artist.name }}</b><div class="small muted">{{ art.batch_name }}</div></div>
        <span class="chev">›</span>
      </RouterLink>

      <div class="card">
        <div class="row between">
          <div>
            <div class="price" v-if="art.sale_status === 'available'">{{ taka(art.price_bdt) }}</div>
            <div v-else><span class="badge" :class="{ dark: art.sale_status === 'sold', warn: art.sale_status === 'reserved' }">{{ saleLabel[art.sale_status] }}</span></div>
          </div>
          <span v-if="!art.is_published" class="badge">Draft — only you can see this</span>
        </div>
        <div class="stack" style="margin-top: .8rem" v-if="!mine">
          <RouterLink v-if="art.live_auction_id" :to="`/auctions/${art.live_auction_id}`" class="btn accent block">
            <Icon name="gavel" /> Go to auction
          </RouterLink>
          <button v-else-if="art.sale_status === 'available'" class="btn accent block" @click="requireLogin() && (buying = true)">
            Request to buy
          </button>
          <button class="btn ghost block" @click="message"><Icon name="chat" /> Message artist</button>
        </div>
        <div class="stack" style="margin-top: .8rem" v-else>
          <RouterLink v-if="art.live_auction_id" :to="`/auctions/${art.live_auction_id}`" class="btn block">View auction</RouterLink>
          <RouterLink v-else-if="!['sold', 'reserved'].includes(art.sale_status)" :to="`/auctions/new?artwork=${art.id}`" class="btn block">
            <Icon name="gavel" /> Start an auction
          </RouterLink>
          <RouterLink :to="`/artworks/${art.id}/edit`" class="btn ghost block"><Icon name="edit" /> Edit details & price</RouterLink>
        </div>
      </div>

      <p v-if="art.description" style="white-space: pre-line">{{ art.description }}</p>
      <button v-if="mine && art.sale_status !== 'sold'" class="btn danger block" @click="remove"><Icon name="trash" /> Delete artwork</button>
    </section>
  </div>
  <div v-else-if="error" class="page"><p class="form-error">{{ error }}</p></div>
  <div v-else class="spinner" />

  <Sheet :open="buying" @close="buying = false">
    <form class="stack" @submit.prevent="placeOrder" v-if="art">
      <h2>Request to buy</h2>
      <p class="small muted">
        Send {{ art.artist.name }} a purchase request for <b>{{ art.title }}</b> at <b>{{ taka(art.price_bdt) }}</b>.
        Once accepted, you'll arrange payment (cash / bKash) and pickup directly with the artist.
      </p>
      <label class="field"><span>Your phone</span><input class="input" v-model="order.contact_phone" type="tel" required /></label>
      <label class="field"><span>Delivery address (optional)</span><textarea class="input" v-model="order.delivery_address" rows="2" /></label>
      <label class="field"><span>Message to the artist</span><textarea class="input" v-model="order.message" rows="3" /></label>
      <button class="btn accent block">Send request</button>
    </form>
  </Sheet>
</template>

<style scoped>
.thumbs { display: flex; gap: .4rem; margin-top: .6rem; overflow-x: auto; }
.thumbs button { width: 56px; height: 56px; padding: 0; border: 2px solid transparent; border-radius: 8px; overflow: hidden; flex: none; background: none; }
.thumbs button.on { border-color: var(--ink); }
.thumbs img { width: 100%; height: 100%; object-fit: cover; }
</style>
