<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import { toast, toastError } from '@/stores/toast'
import { usePoll } from '@/composables/usePoll'
import { taka, dateTime, timeAgo, share } from '@/utils'
import TopBar from '@/components/TopBar.vue'
import Avatar from '@/components/Avatar.vue'
import Countdown from '@/components/Countdown.vue'
import Icon from '@/components/Icon.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuth()
const a = ref(null)
const bids = ref([])
const amount = ref('')
const busy = ref(false)
const error = ref('')

const mine = computed(() => auth.user && a.value?.artwork.artist.id === auth.user.id)
const leading = computed(() => auth.user && a.value?.highest_bid?.bidder.id === auth.user.id)
const iWon = computed(() => auth.user && a.value?.winner?.id === auth.user.id)

async function load() {
  const [auction, b] = await Promise.all([api.get(`/auctions/${route.params.id}/`), api.get(`/auctions/${route.params.id}/bids/`)])
  a.value = auction
  bids.value = b
  if (!amount.value || +amount.value < auction.minimum_next_bid) amount.value = auction.minimum_next_bid
}
onMounted(() => load().catch((e) => (error.value = e.message)))
usePoll(() => (a.value?.phase === 'live' || a.value?.phase === 'scheduled' ? load() : Promise.resolve()), 4000)

async function bid() {
  if (!auth.loggedIn) return router.push({ path: '/login', query: { next: route.fullPath } })
  if (!confirm(`Place a bid of ${taka(amount.value)}? Bids are binding.`)) return
  busy.value = true
  try {
    await api.post(`/auctions/${a.value.id}/bid/`, { amount: +amount.value })
    toast('Bid placed — you are the highest bidder!')
    await load()
  } catch (e) {
    toastError(e)
    await load()
  } finally {
    busy.value = false
  }
}
async function cancel() {
  if (!confirm('Cancel this auction?')) return
  try { await api.post(`/auctions/${a.value.id}/cancel/`); await load() } catch (e) { toastError(e) }
}
async function onShare() {
  if ((await share({ title: `Auction: ${a.value.artwork.title}` })) === 'copied') toast('Link copied')
}
</script>

<template>
  <TopBar title="Auction"><button v-if="a" class="icon-btn" aria-label="Share" @click="onShare"><Icon name="share" /></button></TopBar>
  <div class="page" v-if="a">
    <RouterLink :to="`/artworks/${a.artwork.id}`" class="hero"><img :src="a.artwork.image" :alt="a.artwork.title" /></RouterLink>

    <section class="section stack">
      <div>
        <h1 style="margin-bottom: .2rem">{{ a.artwork.title }}</h1>
        <RouterLink :to="`/artists/${a.artwork.artist.username}`" class="muted">by <b>{{ a.artwork.artist.name }}</b></RouterLink>
      </div>

      <div class="card stack">
        <div class="row between">
          <div>
            <div class="small muted">{{ a.highest_bid ? 'Current bid' : 'Starting price' }}</div>
            <div class="price">{{ taka(a.highest_bid?.amount || a.starting_price) }}</div>
            <div class="tiny faint">{{ a.bid_count }} bids · +{{ taka(a.min_increment) }} increments</div>
          </div>
          <div style="text-align: right">
            <template v-if="a.phase === 'live'">
              <div class="small muted">Ends in</div>
              <div class="price" style="font-size: 1.15rem"><Countdown :to="a.ends_at" :server-time="a.server_time" /></div>
            </template>
            <template v-else-if="a.phase === 'scheduled'">
              <div class="small muted">Starts</div><b>{{ dateTime(a.starts_at) }}</b>
            </template>
            <span v-else class="badge">{{ a.phase === 'cancelled' ? 'Cancelled' : 'Ended' }}</span>
          </div>
        </div>
        <div v-if="a.has_reserve" class="small" :class="a.reserve_met ? 'muted' : ''">
          {{ a.reserve_met ? '✓ Reserve price met' : '• Reserve price not yet met' }}
        </div>

        <template v-if="a.phase === 'live' && !mine">
          <div v-if="leading" class="banner info small">🎉 You're the highest bidder.</div>
          <form class="row" @submit.prevent="bid">
            <input class="input grow" v-model="amount" type="number" inputmode="numeric" :min="a.minimum_next_bid" :step="1" />
            <button class="btn accent" :disabled="busy">Bid</button>
          </form>
          <div class="row">
            <button v-for="k in [0, 1, 3]" :key="k" class="tab grow" type="button" @click="amount = a.minimum_next_bid + k * a.min_increment">
              {{ taka(a.minimum_next_bid + k * a.min_increment) }}
            </button>
          </div>
          <p class="tiny faint" style="margin: 0">Bids in the last minutes extend the auction so everyone gets a fair chance.</p>
        </template>

        <template v-if="a.phase === 'ended'">
          <div v-if="iWon" class="banner info">🏆 You won! Check <RouterLink to="/orders"><b>Orders</b></RouterLink> and message the artist to arrange payment.</div>
          <div v-else-if="a.winner" class="small">Won by <b>{{ a.winner.name }}</b> for {{ taka(a.highest_bid.amount) }}.</div>
          <div v-else class="small muted">Ended without a sale.</div>
        </template>

        <button v-if="mine && a.phase !== 'ended' && a.phase !== 'cancelled' && !a.bid_count" class="btn danger block" @click="cancel">Cancel auction</button>
      </div>

      <div>
        <h3>Bid history</h3>
        <div class="list" v-if="bids.length">
          <div v-for="(b, i) in bids" :key="b.id" class="list-item">
            <Avatar :user="b.bidder" :size="32" />
            <div class="grow"><b>{{ b.bidder.name }}</b><div class="tiny faint">{{ timeAgo(b.created_at) }} ago</div></div>
            <b :style="{ color: i === 0 ? 'var(--accent)' : null }">{{ taka(b.amount) }}</b>
          </div>
        </div>
        <p v-else class="small muted">No bids yet — be the first!</p>
      </div>
    </section>
  </div>
  <div v-else-if="error" class="page"><p class="form-error">{{ error }}</p></div>
  <div v-else class="spinner" />
</template>
