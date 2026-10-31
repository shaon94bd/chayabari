<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, toForm } from '@/api'
import { useAuth } from '@/stores/auth'
import { toast, toastError } from '@/stores/toast'
import TopBar from '@/components/TopBar.vue'
import ImagePicker from '@/components/ImagePicker.vue'
import InactiveBanner from '@/components/InactiveBanner.vue'
import Icon from '@/components/Icon.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuth()
const id = route.params.id
const art = ref(null)
const image = ref(null)
const extra = ref(null)
const f = reactive({
  title: '', medium: '', width_cm: '', height_cm: '', year: new Date().getFullYear(),
  description: '', price_bdt: '', for_sale: false, is_published: true,
})
const error = ref('')
const busy = ref(false)
const locked = computed(() => ['reserved', 'sold'].includes(art.value?.sale_status))

onMounted(async () => {
  if (!id) return
  art.value = await api.get(`/artworks/${id}/`)
  if (art.value.artist.id !== auth.user.id) return router.replace(`/artworks/${id}`)
  for (const k of Object.keys(f)) if (k in art.value) f[k] = art.value[k] ?? ''
  f.width_cm = art.value.width_cm ? +art.value.width_cm : ''
  f.height_cm = art.value.height_cm ? +art.value.height_cm : ''
  f.for_sale = art.value.sale_status === 'available'
})

async function submit() {
  error.value = ''
  busy.value = true
  const data = { ...f, image: image.value || undefined }
  if (locked.value) delete data.for_sale
  try {
    const saved = id ? await api.patch(`/artworks/${id}/`, toForm(data)) : await api.post('/artworks/', toForm(data))
    toast(id ? 'Saved' : 'Artwork uploaded')
    router.replace(`/artworks/${saved.id}`)
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
async function addExtra(file) {
  if (!file) return
  try {
    const img = await api.post(`/artworks/${id}/images/`, toForm({ image: file }))
    art.value.extra_images.push(img)
    extra.value = null
  } catch (e) { toastError(e) }
}
async function removeExtra(img) {
  await api.del(`/artworks/${id}/images/${img.id}/`)
  art.value.extra_images = art.value.extra_images.filter((i) => i.id !== img.id)
}
</script>

<template>
  <TopBar :title="id ? 'Edit artwork' : 'New artwork'" />
  <form class="page no-nav stack" @submit.prevent="submit">
    <InactiveBanner />
    <ImagePicker v-model="image" :current="art?.image" label="Add a photo of your artwork" />
    <p class="tiny faint" style="margin-top: .3rem">Tip: shoot in daylight, straight-on, and crop out the background.</p>

    <label class="field"><span>Title</span><input class="input" v-model="f.title" required /></label>
    <label class="field"><span>Medium</span><input class="input" v-model="f.medium" placeholder="Oil on canvas" /></label>
    <div class="two">
      <label class="field"><span>Width (cm)</span><input class="input" v-model="f.width_cm" type="number" step="0.1" inputmode="decimal" /></label>
      <label class="field"><span>Height (cm)</span><input class="input" v-model="f.height_cm" type="number" step="0.1" inputmode="decimal" /></label>
    </div>
    <label class="field"><span>Year</span><input class="input" v-model="f.year" type="number" inputmode="numeric" /></label>
    <label class="field"><span>About this work</span><textarea class="input" v-model="f.description" rows="4" /></label>

    <div class="card stack">
      <label class="check" v-if="!locked"><input type="checkbox" v-model="f.for_sale" /> Available for sale</label>
      <p v-else class="small muted">This artwork is {{ art.sale_status }} — sale settings are locked.</p>
      <label class="field" v-if="f.for_sale || f.price_bdt"><span>Price (৳ BDT)</span>
        <input class="input" v-model="f.price_bdt" type="number" inputmode="numeric" min="0" :required="f.for_sale" />
      </label>
      <label class="check"><input type="checkbox" v-model="f.is_published" /> Published (visible to others)</label>
    </div>

    <div v-if="id && art" class="card stack">
      <h3>More photos</h3>
      <div class="extras">
        <div v-for="img in art.extra_images" :key="img.id" class="extra">
          <img :src="img.image" alt="" />
          <button type="button" class="icon-btn" aria-label="Remove" @click="removeExtra(img)"><Icon name="trash" /></button>
        </div>
        <div class="extra" v-if="art.extra_images.length < 6">
          <ImagePicker :model-value="extra" @update:model-value="addExtra" label="Add" ratio="1/1" />
        </div>
      </div>
    </div>

    <div v-if="error" class="form-error">{{ error }}</div>
    <button class="btn block" :disabled="busy">{{ busy ? 'Saving…' : id ? 'Save changes' : 'Upload artwork' }}</button>
  </form>
</template>

<style scoped>
.extras { display: grid; grid-template-columns: repeat(3, 1fr); gap: .5rem; }
.extra { position: relative; aspect-ratio: 1; border-radius: 10px; overflow: hidden; }
.extra > img { width: 100%; height: 100%; object-fit: cover; }
.extra .icon-btn { position: absolute; top: 4px; right: 4px; background: rgb(255 255 255 / 85%); width: 32px; height: 32px; }
.extra .icon-btn svg { width: 16px; height: 16px; }
</style>
