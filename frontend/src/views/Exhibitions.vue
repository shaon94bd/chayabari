<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import ExhibitionCard from '@/components/ExhibitionCard.vue'
import GuestBar from '@/components/GuestBar.vue'
import Empty from '@/components/Empty.vue'
import Icon from '@/components/Icon.vue'

const auth = useAuth()
const items = ref([])
const tab = ref('current')
const loading = ref(true)
const shown = computed(() =>
  items.value.filter((e) => (tab.value === 'current' ? e.phase !== 'past' : e.phase === 'past')),
)
onMounted(async () => {
  items.value = (await api.get(`/exhibitions/${auth.batch ? '?mine_batch=1' : ''}`)).results
  loading.value = false
})
</script>

<template>
  <GuestBar />
  <div class="page">
    <div class="row between">
      <h1>Exhibitions</h1>
      <RouterLink v-if="auth.isStudent" to="/exhibitions/new" class="btn sm"><Icon name="plus" /> New</RouterLink>
    </div>
    <div class="tabs">
      <button class="tab" :class="{ on: tab === 'current' }" @click="tab = 'current'">Current & upcoming</button>
      <button class="tab" :class="{ on: tab === 'past' }" @click="tab = 'past'">Past</button>
    </div>
    <div v-if="loading" class="spinner" />
    <div v-else class="stack">
      <ExhibitionCard v-for="e in shown" :key="e.id" :ex="e" />
      <Empty v-if="!shown.length" icon="🏛️" title="No exhibitions" text="Exhibitions curated by batches will show up here." />
    </div>
  </div>
</template>
