<script setup>
import ArtCard from './ArtCard.vue'
defineProps({ items: Array, showArtist: { type: Boolean, default: true } })
</script>

<template>
  <div class="grid">
    <ArtCard v-for="a in items" :key="a.id" :art="a" :show-artist="showArtist" />
  </div>
</template>
