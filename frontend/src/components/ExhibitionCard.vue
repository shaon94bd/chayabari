<script setup>
import { dateShort } from '@/utils'
defineProps({ ex: { type: Object, required: true } })
</script>

<template>
  <RouterLink :to="`/exhibitions/${ex.id}`" class="cover-card">
    <img v-if="ex.cover || ex.cover_fallback" :src="ex.cover || ex.cover_fallback" alt="" loading="lazy" />
    <div class="overlay">
      <div class="row">
        <span class="badge" :class="{ ok: ex.phase === 'ongoing', accent: ex.phase === 'upcoming' }">
          {{ ex.phase === 'ongoing' ? 'On now' : ex.phase === 'upcoming' ? 'Upcoming' : 'Past' }}
        </span>
        <span v-if="!ex.is_published" class="badge">Draft</span>
      </div>
      <h3>{{ ex.title }}</h3>
      <div class="small" style="opacity: .85">
        {{ dateShort(ex.starts_at) }} – {{ dateShort(ex.ends_at) }} · {{ ex.artwork_count }} {{ ex.artwork_count === 1 ? 'work' : 'works' }}
      </div>
    </div>
  </RouterLink>
</template>
