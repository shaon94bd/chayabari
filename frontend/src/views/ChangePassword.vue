<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, tokens } from '@/api'
import { useAuth } from '@/stores/auth'
import { toast } from '@/stores/toast'
import TopBar from '@/components/TopBar.vue'

const auth = useAuth()
const router = useRouter()
const forced = auth.user?.must_change_password
const f = reactive({ current_password: '', new_password: '', confirm: '' })
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  if (f.new_password !== f.confirm) return (error.value = "Passwords don't match.")
  busy.value = true
  try {
    tokens.set(await api.post('/auth/change-password/', { current_password: f.current_password, new_password: f.new_password }))
    await auth.fetchMe()
    toast('Password updated')
    router.replace('/home')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <TopBar title="Change password" :back="!forced" />
  <form class="page no-nav stack" @submit.prevent="submit">
    <div v-if="forced" class="banner info">
      👋 Welcome, {{ auth.user.name }}! Please choose your own password to finish setting up your account.
    </div>
    <label class="field"><span>{{ forced ? 'Temporary password' : 'Current password' }}</span>
      <input class="input" v-model="f.current_password" type="password" autocomplete="current-password" required />
    </label>
    <label class="field"><span>New password</span>
      <input class="input" v-model="f.new_password" type="password" minlength="8" autocomplete="new-password" required />
      <small>At least 8 characters, not too common.</small>
    </label>
    <label class="field"><span>Confirm new password</span>
      <input class="input" v-model="f.confirm" type="password" autocomplete="new-password" required />
    </label>
    <div v-if="error" class="form-error">{{ error }}</div>
    <button class="btn block" :disabled="busy">Save password</button>
    <button v-if="forced" type="button" class="btn ghost block" @click="auth.logout(); router.replace('/login')">Log out</button>
  </form>
</template>
