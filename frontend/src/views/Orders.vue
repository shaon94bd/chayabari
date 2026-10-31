<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import { toast, toastError } from '@/stores/toast'
import { taka, dateShort } from '@/utils'
import TopBar from '@/components/TopBar.vue'
import Avatar from '@/components/Avatar.vue'
import Empty from '@/components/Empty.vue'

const auth = useAuth()
const router = useRouter()
const role = ref(auth.isStudent ? 'seller' : 'buyer')
const orders = ref([])
const loading = ref(true)
const badge = { pending: 'warn', accepted: 'accent', completed: 'ok', rejected: '', cancelled: '' }

async function load() {
  loading.value = true
  orders.value = (await api.get(`/orders/?role=${role.value}`)).results
  loading.value = false
}
watch(role, load)
onMounted(load)

async function act(o, action, confirmText) {
  if (confirmText && !confirm(confirmText)) return
  try {
    Object.assign(o, await api.post(`/orders/${o.id}/${action}/`))
    toast('Updated')
    if (action === 'accept') load()
  } catch (e) { toastError(e) }
}
async function chat(o) {
  const other = role.value === 'seller' ? o.buyer : o.seller
  const c = await api.post('/conversations/direct/', { user_id: other.id })
  router.push({ path: `/chat/${c.id}`, query: { artwork: o.artwork.id } })
}
</script>

<template>
  <TopBar title="Orders" />
  <div class="page">
    <div class="tabs" v-if="auth.isStudent">
      <button class="tab" :class="{ on: role === 'seller' }" @click="role = 'seller'">Selling</button>
      <button class="tab" :class="{ on: role === 'buyer' }" @click="role = 'buyer'">Buying</button>
    </div>
    <div v-if="loading" class="spinner" />
    <div v-else class="stack">
      <div v-for="o in orders" :key="o.id" class="card stack">
        <RouterLink :to="`/artworks/${o.artwork.id}`" class="row">
          <img :src="o.artwork.image" alt="" style="width: 64px; height: 64px; object-fit: cover; border-radius: 10px" />
          <div class="grow">
            <b class="ellipsis" style="display: block">{{ o.artwork.title }}</b>
            <div class="price" style="font-size: 1.1rem">{{ taka(o.amount_bdt) }}</div>
            <div class="tiny faint">{{ o.source === 'auction' ? 'Auction' : 'Direct' }} · {{ dateShort(o.created_at) }}</div>
          </div>
          <span class="badge" :class="badge[o.status]">{{ o.status }}</span>
        </RouterLink>
        <div class="row">
          <Avatar :user="role === 'seller' ? o.buyer : o.seller" :size="28" />
          <span class="small grow">{{ role === 'seller' ? 'Buyer' : 'Artist' }}: <b>{{ (role === 'seller' ? o.buyer : o.seller).name }}</b></span>
          <button class="btn sm ghost" @click="chat(o)">Message</button>
        </div>
        <div v-if="role === 'seller' && (o.message || o.contact_phone || o.delivery_address)" class="small muted">
          <div v-if="o.contact_phone">📞 <a :href="`tel:${o.contact_phone}`">{{ o.contact_phone }}</a></div>
          <div v-if="o.delivery_address">📍 {{ o.delivery_address }}</div>
          <div v-if="o.message">“{{ o.message }}”</div>
        </div>
        <p class="tiny faint" style="margin: 0">{{ o.status_label }}</p>
        <div class="row" v-if="role === 'seller'">
          <template v-if="o.status === 'pending'">
            <button class="btn sm grow" @click="act(o, 'accept')">Accept</button>
            <button class="btn sm ghost grow" @click="act(o, 'reject', 'Decline this request?')">Decline</button>
          </template>
          <template v-if="o.status === 'accepted'">
            <button class="btn sm grow" @click="act(o, 'complete', 'Mark as paid & delivered? The artwork will be marked sold.')">Mark completed</button>
            <button class="btn sm ghost grow" @click="act(o, 'cancel', 'Cancel this sale? The artwork goes back on sale.')">Cancel</button>
          </template>
        </div>
        <div class="row" v-else-if="['pending', 'accepted'].includes(o.status)">
          <button class="btn sm ghost grow" @click="act(o, 'cancel', 'Cancel your request?')">Cancel request</button>
        </div>
      </div>
      <Empty v-if="!orders.length" icon="🧾" :title="role === 'seller' ? 'No sales yet' : 'No purchases yet'"
             :text="role === 'seller' ? 'Put artworks up for sale to receive requests.' : 'Browse artworks and request to buy.'" />
    </div>
  </div>
</template>
