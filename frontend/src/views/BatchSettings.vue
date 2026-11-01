<script setup>
import { ref, reactive, onMounted } from 'vue'
import { api, toForm } from '@/api'
import { useAuth } from '@/stores/auth'
import { toast } from '@/stores/toast'
import TopBar from '@/components/TopBar.vue'
import ImagePicker from '@/components/ImagePicker.vue'

const auth = useAuth()
const f = reactive({ name: '', institution: '', department: '', session: '', about: '' })
const cover = ref(null)
const current = ref(null)
const error = ref('')
const busy = ref(false)

onMounted(async () => {
  const b = await api.get('/batch/')
  Object.keys(f).forEach((k) => (f[k] = b[k] || ''))
  current.value = b.cover
})
async function submit() {
  busy.value = true
  error.value = ''
  try {
    await api.patch('/batch/', toForm({ ...f, cover: cover.value || undefined }))
    await auth.fetchMe()
    toast('Group updated')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <TopBar title="Group settings" />
  <form class="page no-nav stack" @submit.prevent="submit">
    <ImagePicker v-model="cover" :current="current" label="Group cover photo" ratio="16/9" />
    <label class="field"><span>Group name</span><input class="input" v-model="f.name" required /></label>
    <label class="field"><span>Institution</span><input class="input" v-model="f.institution" required /></label>
    <div class="two">
      <label class="field"><span>Department</span><input class="input" v-model="f.department" /></label>
      <label class="field"><span>Session</span><input class="input" v-model="f.session" /></label>
    </div>
    <label class="field"><span>About the group</span><textarea class="input" v-model="f.about" rows="5" /></label>
    <div v-if="error" class="form-error">{{ error }}</div>
    <button class="btn block" :disabled="busy">Save</button>
  </form>
</template>
