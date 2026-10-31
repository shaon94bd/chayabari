<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import { toast } from '@/stores/toast'
import { dateTime, share, taka } from '@/utils'
import TopBar from '@/components/TopBar.vue'
import ArtGrid from '@/components/ArtGrid.vue'
import Sheet from '@/components/Sheet.vue'
import Icon from '@/components/Icon.vue'

const route = useRoute()
const auth = useAuth()
const ex = ref(null)
const error = ref('')
const viewer = ref(null) // index into artworks for the swipe-through "walk" mode

const canEdit = computed(() => auth.user && ex.value && auth.batch?.slug === ex.value.batch_slug &&
  (ex.value.created_by?.id === auth.user.id || auth.isOwner))

onMounted(async () => {
  try { ex.value = await api.get(`/exhibitions/${route.params.id}/`) } catch (e) { error.value = e.message }
})
async function onShare() {
  if ((await share({ title: ex.value.title, text: `${ex.value.title} — ${ex.value.batch_name}` })) === 'copied') toast('Link copied')
}
const current = computed(() => (viewer.value == null ? null : ex.value.artworks[viewer.value]))
let startX = 0
const swipeStart = (e) => (startX = e.touches[0].clientX)
function swipeEnd(e) {
  const dx = e.changedTouches[0].clientX - startX
  if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1)
}
const step = (d) => (viewer.value = (viewer.value + d + ex.value.artworks.length) % ex.value.artworks.length)
</script>

<template>
  <TopBar :title="ex?.title || 'Exhibition'">
    <button v-if="ex" class="icon-btn" aria-label="Share" @click="onShare"><Icon name="share" /></button>
    <RouterLink v-if="canEdit" :to="`/exhibitions/${ex.id}/edit`" class="icon-btn" aria-label="Edit"><Icon name="edit" /></RouterLink>
  </TopBar>
  <div class="page" v-if="ex">
    <div v-if="ex.cover || ex.cover_fallback" class="hero" style="aspect-ratio: 16/10"><img :src="ex.cover || ex.cover_fallback" alt="" style="object-fit: cover" /></div>
    <section class="section stack">
      <div class="row wrap">
        <span class="badge" :class="{ ok: ex.phase === 'ongoing', accent: ex.phase === 'upcoming' }">
          {{ ex.phase === 'ongoing' ? 'On now' : ex.phase === 'upcoming' ? 'Upcoming' : 'Past' }}
        </span>
        <span v-if="!ex.is_published" class="badge">Draft</span>
      </div>
      <h1>{{ ex.title }}</h1>
      <dl class="kv card flat">
        <dt>By</dt><dd><RouterLink :to="`/b/${ex.batch_slug}`"><b>{{ ex.batch_name }}</b></RouterLink></dd>
        <dt>Opens</dt><dd>{{ dateTime(ex.starts_at) }}</dd>
        <dt>Closes</dt><dd>{{ dateTime(ex.ends_at) }}</dd>
        <dt>Venue</dt><dd>{{ ex.venue || 'Online' }}</dd>
        <dt>Curator</dt><dd>{{ ex.created_by?.name }}</dd>
      </dl>
      <p v-if="ex.description" style="white-space: pre-line">{{ ex.description }}</p>
    </section>
    <section class="section">
      <div class="section-head">
        <h2>{{ ex.artworks.length }} works</h2>
        <button v-if="ex.artworks.length" class="btn sm ghost" @click="viewer = 0">▶ Walk through</button>
      </div>
      <ArtGrid :items="ex.artworks" />
    </section>
  </div>
  <div v-else-if="error" class="page"><p class="form-error">{{ error }}</p></div>
  <div v-else class="spinner" />

  <Sheet :open="viewer != null" @close="viewer = null">
    <div v-if="current" @touchstart.passive="swipeStart" @touchend="swipeEnd">
      <div class="walk"><img :src="current.image" :alt="current.title" /></div>
      <div class="row between" style="margin-top: .8rem">
        <button class="icon-btn" @click="step(-1)" aria-label="Previous"><Icon name="back" /></button>
        <div class="center grow">
          <b>{{ current.title }}</b>
          <div class="small muted">{{ current.artist.name }}<span v-if="current.sale_status === 'available'"> · {{ taka(current.price_bdt) }}</span></div>
          <div class="tiny faint">{{ viewer + 1 }} / {{ ex.artworks.length }}</div>
        </div>
        <button class="icon-btn" @click="step(1)" aria-label="Next" style="transform: scaleX(-1)"><Icon name="back" /></button>
      </div>
      <RouterLink :to="`/artworks/${current.id}`" class="btn ghost block" style="margin-top: .6rem">View details</RouterLink>
    </div>
  </Sheet>
</template>

<style scoped>
.walk { height: 58vh; display: grid; place-items: center; background: #e9e2d8; border-radius: 12px; overflow: hidden; }
.walk img { max-height: 100%; object-fit: contain; }
</style>
