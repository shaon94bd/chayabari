<script setup>
import { ref } from 'vue'
import { api } from '@/api'
import { usePoll } from '@/composables/usePoll'
import Icon from './Icon.vue'

const unread = ref(0)
const load = async () => (unread.value = (await api.get('/conversations/unread/')).unread)
load().catch(() => {})
usePoll(load, 20000)
</script>

<template>
  <nav class="nav">
    <div class="nav-inner">
      <RouterLink to="/home"><Icon name="home" />Home</RouterLink>
      <RouterLink to="/explore"><Icon name="search" />Explore</RouterLink>
      <RouterLink to="/auctions"><Icon name="gavel" />Auctions</RouterLink>
      <RouterLink to="/chat">
        <Icon name="chat" />Chat
        <span v-if="unread" class="dot">{{ unread > 99 ? '99+' : unread }}</span>
      </RouterLink>
      <RouterLink to="/me"><Icon name="user" />Me</RouterLink>
    </div>
  </nav>
</template>
