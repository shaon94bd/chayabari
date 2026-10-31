<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import TopBar from '@/components/TopBar.vue'

const auth = useAuth()
const router = useRouter()
const f = reactive({ display_name: '', username: '', password: '', phone: '', email: '' })
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await auth.acceptSession(await api.post('/auth/register/', f))
    router.replace('/explore')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <TopBar title="Collector account" />
  <form class="page no-nav stack" @submit.prevent="submit">
    <div>
      <h1>Collect student art</h1>
      <p class="muted">Bid in auctions, request to buy, and message artists directly.</p>
    </div>
    <label class="field"><span>Your name</span><input class="input" v-model="f.display_name" required /></label>
    <label class="field"><span>Username</span><input class="input" v-model="f.username" autocapitalize="none" required /></label>
    <label class="field"><span>Password</span><input class="input" v-model="f.password" type="password" minlength="8" required /></label>
    <div class="two">
      <label class="field"><span>Phone</span><input class="input" v-model="f.phone" type="tel" /></label>
      <label class="field"><span>Email</span><input class="input" v-model="f.email" type="email" /></label>
    </div>
    <div v-if="error" class="form-error">{{ error }}</div>
    <button class="btn block" :disabled="busy">Create account</button>
    <p class="center small muted">Are you a fine art student? Ask your batch owner for a login.</p>
  </form>
</template>
