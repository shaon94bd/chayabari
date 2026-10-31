<script setup>
defineProps({ icon: { type: String, default: '🖼️' }, title: String, text: String })
</script>

<template>
  <div class="empty">
    <div class="big">{{ icon }}</div>
    <h3>{{ title }}</h3>
    <p class="small" v-if="text">{{ text }}</p>
    <slot />
  </div>
</template>
