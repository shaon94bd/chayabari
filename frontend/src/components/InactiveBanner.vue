<script setup>
import { useAuth } from '@/stores/auth'
const auth = useAuth()
</script>

<template>
  <div v-if="auth.isStudent && !auth.batchActive" class="banner warn">
    <span>⚠️</span>
    <div class="grow small">
      Your batch subscription has expired. Content is read-only and hidden from the public.
      <RouterLink v-if="auth.isOwner" to="/batch/billing"><b>Renew now →</b></RouterLink>
      <span v-else>Ask your batch owner to renew.</span>
    </div>
  </div>
</template>
