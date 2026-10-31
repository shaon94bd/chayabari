<script setup>
import { ref, watch, onMounted } from 'vue'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import { taka, dateTime } from '@/utils'
import Countdown from '@/components/Countdown.vue'
import GuestBar from '@/components/GuestBar.vue'
import Empty from '@/components/Empty.vue'
import Icon from '@/components/Icon.vue'

const auth = useAuth()
const tab = ref('open')
const items = ref([])
const loading = ref(true)
async function load() {
  loading.value = true
  const q = tab.value === 'mine' ? 'mine=1' : `phase=${tab.value}`
  items.value = (await api.get(`/auctions/?${q}`)).results
  loading.value = false
}
watch(tab, load)
onMounted(load)
</script>

<template>
  <GuestBar />
  <div class="page">
    <div class="row between">
      <h1>Auctions</h1>
      <RouterLink v-if="auth.isStudent" to="/auctions/new" class="btn sm"><Icon name="plus" /> New</RouterLink>
    </div>
    <div class="tabs">
      <button class="tab" :class="{ on: tab === 'open' }" @click="tab = 'open'">Live & upcoming</button>
      <button class="tab" :class="{ on: tab === 'ended' }" @click="tab = 'ended'">Ended</button>
      <button v-if="auth.loggedIn" class="tab" :class="{ on: tab === 'mine' }" @click="tab = 'mine'">Mine</button>
    </div>
    <div v-if="loading" class="spinner" />
    <div v-else class="stack">
      <RouterLink v-for="a in items" :key="a.id" :to="`/auctions/${a.id}`" class="card row auction">
        <img :src="a.artwork.image" alt="" />
        <div class="grow">
          <div class="ellipsis"><b>{{ a.artwork.title }}</b></div>
          <div class="small muted ellipsis">{{ a.artwork.artist.name }}</div>
          <div class="row" style="margin-top: .3rem">
            <span class="price" style="font-size: 1.1rem">{{ taka(a.highest_bid?.amount || a.starting_price) }}</span>
            <span class="small faint">{{ a.bid_count }} bids</span>
          </div>
          <div class="small" style="margin-top: .2rem">
            <span v-if="a.phase === 'live'" class="badge accent live">Ends in <Countdown :to="a.ends_at" :server-time="a.server_time" /></span>
            <span v-else-if="a.phase === 'scheduled'" class="badge">Starts {{ dateTime(a.starts_at) }}</span>
            <span v-else-if="a.winner" class="badge ok">Sold</span>
            <span v-else class="badge">{{ a.phase === 'cancelled' ? 'Cancelled' : 'Ended' }}</span>
          </div>
        </div>
      </RouterLink>
      <Empty v-if="!items.length" icon="🔨" title="No auctions" text="When artists auction their work, it shows up here." />
    </div>
  </div>
</template>

<style scoped>
.auction { align-items: stretch; padding: .6rem; }
.auction img { width: 92px; height: 110px; object-fit: cover; border-radius: 10px; flex: none; }
</style>
