<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, toForm } from '@/api'
import { useAuth } from '@/stores/auth'
import { toast, toastError } from '@/stores/toast'
import { toLocalInput, fromLocalInput } from '@/utils'
import TopBar from '@/components/TopBar.vue'
import ImagePicker from '@/components/ImagePicker.vue'
import InactiveBanner from '@/components/InactiveBanner.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuth()
const id = route.params.id
const cover = ref(null)
const currentCover = ref(null)
const now = new Date()
const f = reactive({
  title: '', description: '', venue: '', is_published: true,
  starts_at: toLocalInput(now), ends_at: toLocalInput(new Date(now.getTime() + 7 * 864e5)),
})
const selected = ref([])
const pool = ref([])
const error = ref('')
const busy = ref(false)

onMounted(async () => {
  const all = []
  let url = `/artworks/?batch=${auth.batch.slug}`
  while (url) {
    const res = await api.get(url)
    all.push(...res.results)
    url = res.next ? res.next.replace(/^.*\/api/, '') : null
  }
  // include the user's own unpublished works too
  const mine = (await api.get('/artworks/?mine=1')).results
  for (const m of mine) if (!all.find((a) => a.id === m.id)) all.push(m)
  pool.value = all
  if (id) {
    const ex = await api.get(`/exhibitions/${id}/`)
    Object.assign(f, {
      title: ex.title, description: ex.description, venue: ex.venue, is_published: ex.is_published,
      starts_at: toLocalInput(new Date(ex.starts_at)), ends_at: toLocalInput(new Date(ex.ends_at)),
    })
    currentCover.value = ex.cover
    selected.value = ex.artworks.map((a) => a.id)
  }
})

function toggle(aid) {
  const i = selected.value.indexOf(aid)
  i >= 0 ? selected.value.splice(i, 1) : selected.value.push(aid)
}

async function submit() {
  error.value = ''
  busy.value = true
  try {
    const body = { ...f, starts_at: fromLocalInput(f.starts_at), ends_at: fromLocalInput(f.ends_at), artwork_ids: selected.value }
    let ex = id ? await api.patch(`/exhibitions/${id}/`, body) : await api.post('/exhibitions/', body)
    if (cover.value) ex = await api.patch(`/exhibitions/${ex.id}/`, toForm({ cover: cover.value }))
    toast(id ? 'Saved' : 'Exhibition created')
    router.replace(`/exhibitions/${ex.id}`)
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
async function remove() {
  if (!confirm('Delete this exhibition? Artworks are not deleted.')) return
  try { await api.del(`/exhibitions/${id}/`); router.replace('/exhibitions') } catch (e) { toastError(e) }
}
</script>

<template>
  <TopBar :title="id ? 'Edit exhibition' : 'New exhibition'" />
  <form class="page no-nav stack" @submit.prevent="submit">
    <InactiveBanner />
    <ImagePicker v-model="cover" :current="currentCover" label="Cover image (optional)" ratio="16/10" />
    <label class="field"><span>Title</span><input class="input" v-model="f.title" placeholder="Rivers & Roots — Graduation Show" required /></label>
    <label class="field"><span>Curatorial note</span><textarea class="input" v-model="f.description" rows="4" /></label>
    <label class="field"><span>Venue</span><input class="input" v-model="f.venue" placeholder="Leave empty for online-only" /></label>
    <div class="two">
      <label class="field"><span>Opens</span><input class="input" v-model="f.starts_at" type="datetime-local" required /></label>
      <label class="field"><span>Closes</span><input class="input" v-model="f.ends_at" type="datetime-local" required /></label>
    </div>
    <label class="check"><input type="checkbox" v-model="f.is_published" /> Published (public page)</label>

    <div>
      <div class="section-head"><h3>Select artworks</h3><span class="small muted">{{ selected.length }} selected</span></div>
      <p class="tiny faint">Tap in the order you want them shown.</p>
      <div class="picker-grid">
        <button v-for="a in pool" :key="a.id" type="button" class="pick" :class="{ on: selected.includes(a.id) }" @click="toggle(a.id)">
          <img :src="a.image" :alt="a.title" loading="lazy" />
          <span v-if="selected.includes(a.id)" class="num">{{ selected.indexOf(a.id) + 1 }}</span>
          <span class="cap ellipsis">{{ a.title }}</span>
        </button>
      </div>
      <p v-if="!pool.length" class="small muted">Your batch has no artworks yet.</p>
    </div>

    <div v-if="error" class="form-error">{{ error }}</div>
    <button class="btn block" :disabled="busy">{{ busy ? 'Saving…' : id ? 'Save exhibition' : 'Create exhibition' }}</button>
    <button v-if="id" type="button" class="btn danger block" @click="remove">Delete exhibition</button>
  </form>
</template>

<style scoped>
.picker-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .5rem; }
.pick { position: relative; padding: 0; border: 3px solid transparent; border-radius: 10px; overflow: hidden; aspect-ratio: 1; background: var(--line); cursor: pointer; }
.pick img { width: 100%; height: 100%; object-fit: cover; }
.pick.on { border-color: var(--accent); }
.num { position: absolute; top: 4px; right: 4px; width: 22px; height: 22px; border-radius: 50%; background: var(--accent); color: #fff; font-size: .75rem; font-weight: 700; display: grid; place-items: center; }
.cap { position: absolute; left: 0; right: 0; bottom: 0; background: rgb(0 0 0 / 55%); color: #fff; font-size: .7rem; padding: 2px 4px; }
</style>
