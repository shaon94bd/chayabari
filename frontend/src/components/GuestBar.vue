<script setup>
import { useAuth } from '@/stores/auth'
const auth = useAuth()
const logo = import.meta.env.BASE_URL + "icon.svg"
</script>

<template>
  <header v-if="!auth.loggedIn" class="topbar">
    <div class="topbar-inner">
      <RouterLink to="/" class="brand grow"><img :src="logo" alt="" />Chayabari</RouterLink>
      <RouterLink to="/login" class="btn sm ghost">Log in</RouterLink>
    </div>
  </header>
</template>
