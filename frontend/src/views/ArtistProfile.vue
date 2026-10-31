<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import { toastError } from '@/stores/toast'
import GuestBar from '@/components/GuestBar.vue'
import TopBar from '@/components/TopBar.vue'
import ArtGrid from '@/components/ArtGrid.vue'
import Avatar from '@/components/Avatar.vue'
import Icon from '@/components/Icon.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuth()
const artist = ref(null)
const artworks = ref([])
const error = ref('')
const isMe = () => auth.user?.username === route.params.username

onMounted(async () => {
  try {
    const u = route.params.username
    ;[artist.value, artworks.value] = await Promise.all([
      api.get(`/artists/${u}/`),
      api.get(isMe() ? '/artworks/?mine=1' : `/artworks/?artist=${u}`).then((r) => r.results),
    ])
  } catch (e) { error.value = e.message }
})
async function message() {
  if (!auth.loggedIn) return router.push({ path: '/login', query: { next: route.fullPath } })
  try {
    const c = await api.post('/conversations/direct/', { user_id: artist.value.id })
    router.push(`/chat/${c.id}`)
  } catch (e) { toastError(e) }
}
</script>

<template>
  <GuestBar />
  <TopBar v-if="auth.loggedIn" :title="artist?.name || 'Artist'" />
  <div class="page" v-if="artist">
    <div class="center stack">
      <Avatar :user="artist" :size="96" style="margin: 0 auto" />
      <div>
        <h1 style="margin: 0">{{ artist.name }}</h1>
        <RouterLink :to="`/b/${artist.batch.slug}`" class="small muted">{{ artist.batch.name }} · {{ artist.batch.institution }}</RouterLink>
      </div>
      <p v-if="artist.bio" style="white-space: pre-line">{{ artist.bio }}</p>
      <div class="row" style="justify-content: center">
        <RouterLink v-if="isMe()" to="/me/edit" class="btn sm ghost"><Icon name="edit" /> Edit profile</RouterLink>
        <RouterLink v-if="isMe()" to="/artworks/new" class="btn sm"><Icon name="plus" /> Artwork</RouterLink>
        <button v-else class="btn sm" @click="message"><Icon name="chat" /> Message</button>
      </div>
    </div>
    <section class="section">
      <h2>{{ artworks.length }} {{ artworks.length === 1 ? 'artwork' : 'artworks' }}</h2>
      <ArtGrid :items="artworks" :show-artist="false" />
    </section>
  </div>
  <div v-else-if="error" class="page"><p class="form-error">{{ error }}</p></div>
  <div v-else class="spinner" />
</template>
