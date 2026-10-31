<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import TopBar from '@/components/TopBar.vue'

const auth = useAuth()
const router = useRouter()
const f = reactive({
  batch_name: '', institution: '', department: 'Fine Art', session: '',
  display_name: '', username: '', password: '', phone: '', email: '',
})
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await auth.acceptSession(await api.post('/signup/', f))
    router.replace('/batch/members?welcome=1')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <TopBar title="Start your batch" />
  <form class="page no-nav stack" @submit.prevent="submit">
    <div>
      <h1>Create your batch</h1>
      <p class="muted">14 days free. You'll add your classmates next.</p>
    </div>
    <div class="card stack">
      <h3>Batch</h3>
      <label class="field"><span>Batch name</span>
        <input class="input" v-model="f.batch_name" placeholder="e.g. JU Fine Art — Batch 47" required />
      </label>
      <label class="field"><span>University / institute</span>
        <input class="input" v-model="f.institution" placeholder="Jahangirnagar University" required />
      </label>
      <div class="two">
        <label class="field"><span>Department</span><input class="input" v-model="f.department" /></label>
        <label class="field"><span>Session</span><input class="input" v-model="f.session" placeholder="2021-22" /></label>
      </div>
    </div>
    <div class="card stack">
      <h3>You (batch owner)</h3>
      <label class="field"><span>Your name</span><input class="input" v-model="f.display_name" required /></label>
      <label class="field"><span>Username</span>
        <input class="input" v-model="f.username" autocapitalize="none" autocomplete="username" required />
      </label>
      <label class="field"><span>Password</span>
        <input class="input" v-model="f.password" type="password" minlength="8" autocomplete="new-password" required />
        <small>At least 8 characters.</small>
      </label>
      <div class="two">
        <label class="field"><span>Phone</span><input class="input" v-model="f.phone" type="tel" /></label>
        <label class="field"><span>Email</span><input class="input" v-model="f.email" type="email" /></label>
      </div>
    </div>
    <div v-if="error" class="form-error">{{ error }}</div>
    <button class="btn accent block" :disabled="busy">{{ busy ? 'Creating…' : 'Create batch & start trial' }}</button>
  </form>
</template>
