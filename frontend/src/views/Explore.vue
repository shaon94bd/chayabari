<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import ArtGrid from '@/components/ArtGrid.vue'
import GuestBar from '@/components/GuestBar.vue'
import Empty from '@/components/Empty.vue'

const auth = useAuth()
const q = ref('')
const route = useRoute()
const filter = ref(route.query.mine ? 'mine' : route.query.sale ? 'sale' : 'all')
const items = ref([])
const next = ref(null)
const loading = ref(false)

function query() {
  const p = new URLSearchParams()
  if (q.value) p.set('q', q.value)
  if (filter.value === 'sale') p.set('for_sale', '1')
  if (filter.value === 'batch' && auth.batch) p.set('batch', auth.batch.slug)
  if (filter.value === 'mine') p.set('mine', '1')
  return p.toString()
}
async function load(reset = true) {
  loading.value = true
  const res = await api.get(reset ? `/artworks/?${query()}` : next.value.replace(/^.*\/api/, ''))
  items.value = reset ? res.results : [...items.value, ...res.results]
  next.value = res.next
  loading.value = false
}
let t
watch(q, () => { clearTimeout(t); t = setTimeout(load, 350) })
watch(filter, () => load())
onMounted(load)
</script>

<template>
  <GuestBar />
  <div class="page">
    <h1>Explore</h1>
    <input class="input" v-model="q" type="search" placeholder="Search title, medium, artist…" style="margin-bottom: .75rem" />
    <div class="tabs">
      <button class="tab" :class="{ on: filter === 'all' }" @click="filter = 'all'">All</button>
      <button class="tab" :class="{ on: filter === 'sale' }" @click="filter = 'sale'">For sale</button>
      <button v-if="auth.batch" class="tab" :class="{ on: filter === 'batch' }" @click="filter = 'batch'">My group</button>
      <button v-if="auth.isStudent" class="tab" :class="{ on: filter === 'mine' }" @click="filter = 'mine'">Mine</button>
      <RouterLink class="tab" to="/exhibitions" style="display: grid; place-items: center">Exhibitions →</RouterLink>
    </div>
    <ArtGrid :items="items" />
    <Empty v-if="!loading && !items.length" title="Nothing here yet" text="Try a different search." />
    <div v-if="loading" class="spinner" />
    <button v-else-if="next" class="btn ghost block section" @click="load(false)">Load more</button>
  </div>
</template>
