<script setup>
import { useRouter } from 'vue-router'
import Icon from './Icon.vue'

defineProps({ title: String, back: { type: Boolean, default: true } })
const router = useRouter()
const goBack = () => (window.history.state?.back ? router.back() : router.push('/home'))
</script>

<template>
  <header class="topbar">
    <div class="topbar-inner">
      <button v-if="back" class="icon-btn" aria-label="Back" @click="goBack"><Icon name="back" /></button>
      <div class="topbar-title">{{ title }}</div>
      <slot />
    </div>
  </header>
</template>
