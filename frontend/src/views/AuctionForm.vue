<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { toast } from '@/stores/toast'
import { toLocalInput, fromLocalInput, taka } from '@/utils'
import TopBar from '@/components/TopBar.vue'
import InactiveBanner from '@/components/InactiveBanner.vue'

const route = useRoute()
const router = useRouter()
const mine = ref([])
const now = new Date()
const f = reactive({
  artwork_id: route.query.artwork ? +route.query.artwork : null,
  starting_price: '', min_increment: 500, reserve_price: '',
  starts_at: toLocalInput(now), ends_at: toLocalInput(new Date(now.getTime() + 3 * 864e5)),
})
const error = ref('')
const busy = ref(false)
const eligible = computed(() => mine.value.filter((a) => !['sold', 'reserved'].includes(a.sale_status)))

onMounted(async () => {
  mine.value = (await api.get('/artworks/?mine=1')).results
  const art = mine.value.find((a) => a.id === f.artwork_id)
  if (art?.price_bdt && !f.starting_price) f.starting_price = Math.round(art.price_bdt * 0.6)
})

async function submit() {
  error.value = ''
  busy.value = true
  try {
    const a = await api.post('/auctions/', {
      ...f, reserve_price: f.reserve_price || null,
      starts_at: fromLocalInput(f.starts_at), ends_at: fromLocalInput(f.ends_at),
    })
    toast('Auction created')
    router.replace(`/auctions/${a.id}`)
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <TopBar title="New auction" />
  <form class="page no-nav stack" @submit.prevent="submit">
    <InactiveBanner />
    <div>
      <h3>Choose an artwork</h3>
      <div class="pick-row">
        <button v-for="a in eligible" :key="a.id" type="button" class="pick" :class="{ on: f.artwork_id === a.id }" @click="f.artwork_id = a.id">
          <img :src="a.image" :alt="a.title" />
          <span class="ellipsis small">{{ a.title }}</span>
        </button>
      </div>
      <p v-if="!eligible.length" class="small muted">You have no artworks available. <RouterLink to="/artworks/new"><b>Upload one</b></RouterLink></p>
    </div>
    <div class="two">
      <label class="field"><span>Starting price (৳)</span><input class="input" v-model="f.starting_price" type="number" inputmode="numeric" min="1" required /></label>
      <label class="field"><span>Min. increment (৳)</span><input class="input" v-model="f.min_increment" type="number" inputmode="numeric" min="1" required /></label>
    </div>
    <label class="field"><span>Reserve price (৳, optional)</span>
      <input class="input" v-model="f.reserve_price" type="number" inputmode="numeric" />
      <small>Hidden from bidders. If bidding doesn't reach it, the artwork isn't sold.</small>
    </label>
    <div class="two">
      <label class="field"><span>Starts</span><input class="input" v-model="f.starts_at" type="datetime-local" required /></label>
      <label class="field"><span>Ends</span><input class="input" v-model="f.ends_at" type="datetime-local" required /></label>
    </div>
    <p class="tiny faint">When the auction ends, the highest bidder gets an order{{ f.starting_price ? ` (from ${taka(f.starting_price)})` : '' }} and you arrange payment & handover together.</p>
    <div v-if="error" class="form-error">{{ error }}</div>
    <button class="btn block" :disabled="busy || !f.artwork_id">Start auction</button>
  </form>
</template>

<style scoped>
.pick-row { display: flex; gap: .6rem; overflow-x: auto; padding-bottom: .3rem; }
.pick { flex: 0 0 110px; padding: 0; border: 3px solid transparent; border-radius: 12px; overflow: hidden; background: var(--card); cursor: pointer; text-align: left; }
.pick img { width: 100%; aspect-ratio: 1; object-fit: cover; }
.pick span { display: block; padding: .25rem .4rem; }
.pick.on { border-color: var(--accent); }
</style>
