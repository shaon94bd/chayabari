<script setup>
import Empty from '@/components/Empty.vue'
</script>

<template>
  <div class="page no-nav">
    <Empty icon="🧭" title="Page not found" text="This page doesn't exist or is no longer available.">
      <RouterLink to="/" class="btn">Go home</RouterLink>
    </Empty>
  </div>
</template>
