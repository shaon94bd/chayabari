<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from './stores/auth'
import { toasts } from './stores/toast'
import BottomNav from './components/BottomNav.vue'

const route = useRoute()
const auth = useAuth()
const showNav = computed(() => route.meta.nav && auth.loggedIn)
</script>

<template>
  <RouterView v-slot="{ Component }">
    <component :is="Component" :key="route.path" />
  </RouterView>
  <BottomNav v-if="showNav" />
  <div class="toasts" :style="showNav ? null : { bottom: '16px' }">
    <div v-for="t in toasts" :key="t.id" class="toast" :class="t.kind">{{ t.message }}</div>
  </div>
</template>
