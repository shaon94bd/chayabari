<script setup>
import { taka, saleLabel } from '@/utils'
defineProps({ art: { type: Object, required: true }, showArtist: { type: Boolean, default: true } })
</script>

<template>
  <RouterLink :to="`/artworks/${art.id}`" class="art-card">
    <div class="thumb">
      <img :src="art.image" :alt="art.title" loading="lazy" />
      <span v-if="art.sale_status === 'sold'" class="badge dark">Sold</span>
      <span v-else-if="art.sale_status === 'reserved'" class="badge warn">Reserved</span>
      <span v-else-if="!art.is_published" class="badge">Draft</span>
    </div>
    <div class="meta">
      <div class="title">{{ art.title }}</div>
      <div class="small muted ellipsis" v-if="showArtist">{{ art.artist?.name }}</div>
      <div class="small" v-if="art.sale_status === 'available'"><b>{{ taka(art.price_bdt) }}</b></div>
      <div class="small faint" v-else>{{ saleLabel[art.sale_status] }}</div>
    </div>
  </RouterLink>
</template>
