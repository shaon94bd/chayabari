<script setup>
import { ref, reactive, onMounted } from 'vue'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import { toast } from '@/stores/toast'
import { taka, dateShort } from '@/utils'
import TopBar from '@/components/TopBar.vue'
import Sheet from '@/components/Sheet.vue'

const auth = useAuth()
const info = ref(null)
const plans = ref([])
const paying = ref(null)
const f = reactive({ method: 'bkash', transaction_id: '', sender_number: '' })
const error = ref('')
const busy = ref(false)
const statusLabel = { trial: 'Free trial', pending: 'Awaiting verification', active: 'Active', cancelled: 'Cancelled' }

async function load() {
  ;[info.value, plans.value] = await Promise.all([api.get('/batch/subscription/'), api.get('/plans/')])
}
onMounted(load)
const pending = () => info.value?.history.find((s) => s.status === 'pending')

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await api.post('/batch/subscription/checkout/', { plan: paying.value.id, ...f })
    paying.value = null
    toast('Payment submitted! We will verify it shortly.')
    await Promise.all([load(), auth.fetchMe()])
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <TopBar title="Subscription" />
  <div class="page no-nav stack" v-if="info">
    <div class="card">
      <div class="row between">
        <div>
          <div class="small muted">Current plan</div>
          <h2 style="margin: 0">{{ info.current ? info.current.plan?.name || 'Free trial' : 'No active plan' }}</h2>
        </div>
        <span class="badge" :class="info.is_active ? 'ok' : 'warn'">{{ info.is_active ? 'Active' : 'Expired' }}</span>
      </div>
      <div v-if="info.current" class="small muted" style="margin-top: .3rem">Valid until <b>{{ dateShort(info.current.ends_at) }}</b></div>
      <div class="small muted">{{ info.seats_used }} of {{ info.seats_total }} member seats used</div>
    </div>

    <div v-if="pending()" class="banner info small">
      ⏳ Your {{ pending().payment?.method }} payment ({{ pending().payment?.transaction_id }}) is being verified. This usually takes a few hours.
    </div>

    <template v-if="auth.isOwner">
      <h3 class="section">Plans</h3>
      <div v-for="p in plans" :key="p.id" class="card stack">
        <div class="row between">
          <div><h3 style="margin: 0">{{ p.name }}</h3><div class="small muted">{{ Math.round(p.duration_days / 30) }} months · up to {{ p.max_members }} members</div></div>
          <div class="price">{{ taka(p.price_bdt) }}</div>
        </div>
        <p class="small muted" style="margin: 0">{{ p.description }}</p>
        <div class="tiny faint">≈ {{ taka(Math.ceil(p.price_bdt / 30)) }} per student for a group of 30</div>
        <button class="btn block" :disabled="!!pending()" @click="paying = p">Pay with bKash / Nagad</button>
      </div>
    </template>
    <p v-else class="small muted">Only the group owner can manage the subscription.</p>

    <template v-if="info.history.length">
      <h3 class="section">History</h3>
      <div class="list">
        <div v-for="s in info.history" :key="s.id" class="list-item">
          <div class="grow">
            <b>{{ s.plan?.name || 'Free trial' }}</b>
            <div class="tiny faint">
              <span v-if="s.starts_at">{{ dateShort(s.starts_at) }} – {{ dateShort(s.ends_at) }}</span>
              <span v-else>Submitted {{ dateShort(s.created_at) }}</span>
              <span v-if="s.payment"> · {{ s.payment.method }} {{ s.payment.transaction_id }}</span>
            </div>
          </div>
          <span class="badge" :class="{ ok: s.status === 'active', warn: s.status === 'pending' }">{{ statusLabel[s.status] }}</span>
        </div>
      </div>
    </template>
  </div>
  <div v-else class="spinner" />

  <Sheet :open="!!paying" @close="paying = null">
    <form v-if="paying" class="stack" @submit.prevent="submit">
      <h2>Pay {{ taka(paying.price_bdt) }}</h2>
      <ol class="small muted" style="padding-left: 1.2rem; margin: 0">
        <li>Open your {{ f.method === 'nagad' ? 'Nagad' : 'bKash' }} app and choose <b>Send Money</b>.</li>
        <li>Send <b>{{ taka(paying.price_bdt) }}</b> to <b>{{ info.payment_numbers[f.method] || info.payment_numbers.bkash }}</b>.</li>
        <li>Enter the Transaction ID (TrxID) from the confirmation SMS below.</li>
      </ol>
      <div class="tabs" style="margin: 0">
        <button type="button" class="tab" :class="{ on: f.method === 'bkash' }" @click="f.method = 'bkash'">bKash</button>
        <button type="button" class="tab" :class="{ on: f.method === 'nagad' }" @click="f.method = 'nagad'">Nagad</button>
      </div>
      <label class="field"><span>Transaction ID</span><input class="input" v-model="f.transaction_id" autocapitalize="characters" required /></label>
      <label class="field"><span>Your {{ f.method === 'nagad' ? 'Nagad' : 'bKash' }} number</span><input class="input" v-model="f.sender_number" type="tel" required /></label>
      <div v-if="error" class="form-error">{{ error }}</div>
      <button class="btn accent block" :disabled="busy">Submit payment</button>
      <p class="tiny faint center" style="margin: 0">Your plan activates as soon as we verify the payment. Remaining time is never lost — paid time starts after your current plan.</p>
    </form>
  </Sheet>
</template>
