<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import { taka } from '@/utils'
import ArtGrid from '@/components/ArtGrid.vue'
import ExhibitionCard from '@/components/ExhibitionCard.vue'
import Countdown from '@/components/Countdown.vue'
import InactiveBanner from '@/components/InactiveBanner.vue'
import Icon from '@/components/Icon.vue'

const auth = useAuth()
const exhibitions = ref([])
const auctions = ref([])
const artworks = ref([])
const loading = ref(true)

onMounted(async () => {
  const b = auth.batch?.slug
  const [ex, au, ar] = await Promise.all([
    api.get(b ? `/exhibitions/?mine_batch=1` : '/exhibitions/'),
    api.get('/auctions/?phase=open'),
    api.get(b ? `/artworks/?batch=${b}` : '/artworks/?for_sale=1'),
  ])
  exhibitions.value = ex.results.filter((e) => e.phase !== 'past').slice(0, 6)
  auctions.value = au.results.slice(0, 8)
  artworks.value = ar.results.slice(0, 12)
  loading.value = false
})
</script>

<template>
  <div class="page">
    <header class="row between" style="margin-bottom: 1rem">
      <div class="grow">
        <div class="small muted">{{ auth.batch?.name || 'Collector' }}</div>
        <h1 style="margin: 0">Hi, {{ auth.user.name.split(' ')[0] }}</h1>
      </div>
      <RouterLink v-if="auth.batch" :to="`/b/${auth.batch.slug}`" class="icon-btn" aria-label="Group page"><Icon name="globe" /></RouterLink>
    </header>

    <InactiveBanner />

    <div v-if="auth.isStudent" class="quick">
      <RouterLink to="/artworks/new" class="card quick-item"><Icon name="plus" /><span>Artwork</span></RouterLink>
      <RouterLink to="/exhibitions/new" class="card quick-item"><Icon name="frame" /><span>Exhibition</span></RouterLink>
      <RouterLink to="/auctions/new" class="card quick-item"><Icon name="gavel" /><span>Auction</span></RouterLink>
    </div>

    <div v-if="loading" class="spinner" />
    <template v-else>
      <section class="section">
        <div class="section-head"><h2>Exhibitions</h2><RouterLink to="/exhibitions">All</RouterLink></div>
        <div v-if="exhibitions.length" class="hscroll">
          <ExhibitionCard v-for="e in exhibitions" :key="e.id" :ex="e" />
        </div>
        <p v-else class="small muted">No current exhibitions.
          <RouterLink v-if="auth.isStudent" to="/exhibitions/new"><b>Curate one →</b></RouterLink></p>
      </section>

      <section class="section" v-if="auctions.length">
        <div class="section-head"><h2>Auctions</h2><RouterLink to="/auctions">All</RouterLink></div>
        <div class="list">
          <RouterLink v-for="a in auctions" :key="a.id" :to="`/auctions/${a.id}`" class="list-item">
            <img :src="a.artwork.image" alt="" style="width: 48px; height: 48px; border-radius: 8px; object-fit: cover" />
            <div class="grow">
              <div class="ellipsis"><b>{{ a.artwork.title }}</b></div>
              <div class="small muted">{{ taka(a.highest_bid?.amount || a.starting_price) }} · {{ a.bid_count }} bids</div>
            </div>
            <span v-if="a.phase === 'live'" class="badge accent live"><Countdown :to="a.ends_at" :server-time="a.server_time" /></span>
            <span v-else class="badge">Soon</span>
          </RouterLink>
        </div>
      </section>

      <section class="section">
        <div class="section-head">
          <h2>{{ auth.batch ? 'From your group' : 'For sale' }}</h2>
          <RouterLink to="/explore">Explore</RouterLink>
        </div>
        <ArtGrid v-if="artworks.length" :items="artworks" />
        <p v-else class="small muted">No artworks yet.
          <RouterLink v-if="auth.isStudent" to="/artworks/new"><b>Upload your first →</b></RouterLink></p>
      </section>
    </template>
  </div>
</template>

<style scoped>
.quick { display: grid; grid-template-columns: repeat(3, 1fr); gap: .6rem; margin-top: .8rem; }
.quick-item { display: flex; flex-direction: column; align-items: center; gap: .3rem; padding: .85rem .5rem; font-size: .85rem; font-weight: 600; }
.quick-item svg { width: 22px; height: 22px; color: var(--accent); }
</style>
