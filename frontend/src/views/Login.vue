<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/stores/auth'
import TopBar from '@/components/TopBar.vue'

const auth = useAuth()
const router = useRouter()
const route = useRoute()
const username = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await auth.login(username.value, password.value)
    router.replace(auth.user.must_change_password ? '/change-password' : route.query.next || '/home')
  } catch (e) {
    error.value = e.status === 401 ? 'Wrong username or password.' : e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <TopBar title="Log in" />
  <form class="page no-nav stack" @submit.prevent="submit">
    <h1>Welcome back</h1>
    <p class="muted">Use the username and password your batch owner gave you.</p>
    <label class="field"><span>Username</span>
      <input class="input" v-model="username" autocomplete="username" autocapitalize="none" required />
    </label>
    <label class="field"><span>Password</span>
      <input class="input" v-model="password" type="password" autocomplete="current-password" required />
    </label>
    <div v-if="error" class="form-error">{{ error }}</div>
    <button class="btn block" :disabled="busy">{{ busy ? 'Logging in…' : 'Log in' }}</button>
    <p class="center small muted">
      New batch? <RouterLink to="/signup"><b>Start your batch</b></RouterLink><br />
      Buying art? <RouterLink to="/register"><b>Create a collector account</b></RouterLink>
    </p>
    <p class="center tiny faint">Forgot your password? Ask your batch owner to reset it from the Members page.</p>
  </form>
</template>
