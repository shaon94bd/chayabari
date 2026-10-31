<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api'
import { toast } from '@/stores/toast'
import { share } from '@/utils'
import GuestBar from '@/components/GuestBar.vue'
import TopBar from '@/components/TopBar.vue'
import ArtGrid from '@/components/ArtGrid.vue'
import ExhibitionCard from '@/components/ExhibitionCard.vue'
import Avatar from '@/components/Avatar.vue'
import Icon from '@/components/Icon.vue'
import { useAuth } from '@/stores/auth'

const route = useRoute()
const auth = useAuth()
const slug = route.params.slug
const batch = ref(null)
const exhibitions = ref([])
const artworks = ref([])
const error = ref('')

onMounted(async () => {
  try {
    const [b, ex, ar] = await Promise.all([
      api.get(`/public/batches/${slug}/`), api.get(`/exhibitions/?batch=${slug}`), api.get(`/artworks/?batch=${slug}`),
    ])
    batch.value = b
    exhibitions.value = ex.results.filter((e) => e.is_published)
    artworks.value = ar.results.filter((a) => a.is_published)
  } catch (e) { error.value = e.message }
})
async function onShare() {
  if ((await share({ title: batch.value.name })) === 'copied') toast('Link copied')
}
</script>

<template>
  <GuestBar />
  <TopBar v-if="auth.loggedIn" :title="batch?.name || 'Batch'"><button class="icon-btn" @click="onShare" aria-label="Share"><Icon name="share" /></button></TopBar>
  <div class="page" v-if="batch">
    <div class="hero" style="aspect-ratio: 16/8" v-if="batch.cover"><img :src="batch.cover" alt="" style="object-fit: cover" /></div>
    <section class="section">
      <div class="small muted">{{ batch.institution }} · {{ batch.department }}<span v-if="batch.session"> · {{ batch.session }}</span></div>
      <h1>{{ batch.name }}</h1>
      <p v-if="batch.about" class="muted" style="white-space: pre-line">{{ batch.about }}</p>
      <div class="row small muted"><span>{{ batch.artists.length }} artists</span>·<span>{{ batch.artists.reduce((n, a) => n + a.artwork_count, 0) }} artworks</span></div>
    </section>

    <section class="section" v-if="exhibitions.length">
      <h2>Exhibitions</h2>
      <div class="hscroll"><ExhibitionCard v-for="e in exhibitions" :key="e.id" :ex="e" /></div>
    </section>

    <section class="section">
      <h2>Artists</h2>
      <div class="hscroll artists">
        <RouterLink v-for="a in batch.artists" :key="a.id" :to="`/artists/${a.username}`" class="center">
          <Avatar :user="a" :size="64" style="margin: 0 auto .3rem" />
          <div class="small ellipsis"><b>{{ a.name }}</b></div>
          <div class="tiny faint">{{ a.artwork_count }} {{ a.artwork_count === 1 ? 'work' : 'works' }}</div>
        </RouterLink>
      </div>
    </section>

    <section class="section">
      <h2>Artworks</h2>
      <ArtGrid :items="artworks" />
    </section>
  </div>
  <div v-else-if="error" class="page"><p class="form-error">{{ error }}</p></div>
  <div v-else class="spinner" />
</template>

<style scoped>
.artists > * { flex: 0 0 84px !important; }
</style>
