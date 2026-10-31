<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { api, toForm } from '@/api'
import { useAuth } from '@/stores/auth'
import { toast } from '@/stores/toast'
import TopBar from '@/components/TopBar.vue'
import ImagePicker from '@/components/ImagePicker.vue'

const auth = useAuth()
const router = useRouter()
const u = auth.user
const f = reactive({ display_name: u.display_name, bio: u.bio, phone: u.phone, email: u.email })
const avatar = ref(null)
const error = ref('')
const busy = ref(false)

async function submit() {
  busy.value = true
  error.value = ''
  try {
    auth.user = await api.patch('/auth/me/', toForm({ ...f, avatar: avatar.value || undefined }))
    toast('Profile saved')
    router.back()
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <TopBar title="Edit profile" />
  <form class="page no-nav stack" @submit.prevent="submit">
    <div style="width: 140px; margin: 0 auto"><ImagePicker v-model="avatar" :current="u.avatar" label="Photo" ratio="1/1" /></div>
    <label class="field"><span>Name</span><input class="input" v-model="f.display_name" /></label>
    <label class="field"><span>Bio / artist statement</span><textarea class="input" v-model="f.bio" rows="4" /></label>
    <label class="field"><span>Phone</span><input class="input" v-model="f.phone" type="tel" /><small>Never shown publicly.</small></label>
    <label class="field"><span>Email</span><input class="input" v-model="f.email" type="email" /></label>
    <div v-if="error" class="form-error">{{ error }}</div>
    <button class="btn block" :disabled="busy">Save</button>
  </form>
</template>
