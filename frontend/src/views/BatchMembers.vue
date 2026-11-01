<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'
import { toast, toastError } from '@/stores/toast'
import TopBar from '@/components/TopBar.vue'
import Avatar from '@/components/Avatar.vue'
import Sheet from '@/components/Sheet.vue'
import Icon from '@/components/Icon.vue'
import InactiveBanner from '@/components/InactiveBanner.vue'

const auth = useAuth()
const route = useRoute()
const router = useRouter()
const members = ref([])
const sub = ref(null)
const adding = ref(false)
const names = ref('')
const credentials = ref([])
const selected = ref(null)
const busy = ref(false)
const welcome = !!route.query.welcome

const parsed = computed(() =>
  names.value.split('\n').map((l) => l.trim()).filter(Boolean).map((line) => {
    // "Full Name, username, phone" — username & phone optional
    const [display_name, username = '', phone = ''] = line.split(',').map((s) => s.trim())
    return { display_name, username, phone }
  }),
)
const loginUrl = location.origin + '/login'

async function load() {
  members.value = await api.get('/batch/members/')
  if (auth.isOwner) sub.value = await api.get('/batch/subscription/')
}
onMounted(load)

async function add() {
  busy.value = true
  try {
    const res = await api.post('/batch/members/', { members: parsed.value })
    credentials.value = res.credentials
    names.value = ''
    adding.value = false
    await load()
  } catch (e) { toastError(e) } finally { busy.value = false }
}
const credText = (c) => `Chayabari login for ${c.name}\n${loginUrl}\nUsername: ${c.username}\nPassword: ${c.password}\n(You'll set your own password after logging in.)`
async function copy(text) { await navigator.clipboard.writeText(text); toast('Copied') }
const whatsapp = (c) => `https://wa.me/?text=${encodeURIComponent(credText(c))}`

async function reset(m) {
  if (!confirm(`Reset ${m.name}'s password? Their old password will stop working.`)) return
  try { credentials.value = [await api.post(`/batch/members/${m.id}/reset-password/`)]; selected.value = null } catch (e) { toastError(e) }
}
async function toggleActive(m) {
  try {
    Object.assign(m, await api.patch(`/batch/members/${m.id}/`, { is_active: !m.is_active }))
    selected.value = null
    toast(m.is_active ? 'Reactivated' : 'Deactivated')
  } catch (e) { toastError(e) }
}
async function makeOwner(m) {
  if (!confirm(`Make ${m.name} the group owner? You will become a regular member.`)) return
  try {
    await api.post(`/batch/members/${m.id}/make-owner/`)
    await auth.fetchMe()
    router.replace('/me')
  } catch (e) { toastError(e) }
}
async function startChat(m) {
  const c = await api.post('/conversations/direct/', { user_id: m.id })
  router.push(`/chat/${c.id}`)
}
</script>

<template>
  <TopBar title="Members">
    <button v-if="auth.isOwner" class="icon-btn" aria-label="Add members" @click="adding = true"><Icon name="plus" /></button>
  </TopBar>
  <div class="page no-nav stack">
    <InactiveBanner />
    <div v-if="welcome && members.length <= 1" class="card stack">
      <h2>🎉 Your group is ready!</h2>
      <p class="small muted" style="margin: 0">Next: add your classmates. We'll generate a username and password for each — share them privately (WhatsApp works great).</p>
      <button class="btn accent block" @click="adding = true"><Icon name="users" /> Add classmates</button>
    </div>
    <div v-if="sub" class="row between small muted">
      <span>{{ sub.seats_used }} / {{ sub.seats_total }} seats used</span>
      <RouterLink to="/group/billing" style="color: var(--accent)">Subscription →</RouterLink>
    </div>

    <div class="list">
      <component :is="auth.isOwner && m.id !== auth.user.id ? 'button' : 'div'" v-for="m in members" :key="m.id" class="list-item"
                 :style="{ opacity: m.is_active ? 1 : .5 }" @click="auth.isOwner && m.id !== auth.user.id && (selected = m)">
        <Avatar :user="m" :size="40" />
        <div class="grow">
          <div class="row"><b class="ellipsis">{{ m.name }}</b><span v-if="m.role === 'owner'" class="badge dark">Owner</span></div>
          <div class="tiny faint">@{{ m.username }}
            <template v-if="auth.isOwner">
              · <span v-if="!m.is_active">deactivated</span>
              <span v-else-if="!m.last_login">hasn't logged in</span>
              <span v-else-if="m.must_change_password">using temp password</span>
              <span v-else>active</span>
            </template>
          </div>
        </div>
        <button v-if="!auth.isOwner && m.id !== auth.user.id" class="btn sm ghost" @click.stop="startChat(m)">Message</button>
        <span v-else-if="auth.isOwner && m.id !== auth.user.id" class="chev">›</span>
      </component>
    </div>
  </div>

  <Sheet :open="adding" @close="adding = false">
    <form class="stack" @submit.prevent="add">
      <h2>Add classmates</h2>
      <p class="small muted" style="margin: 0">One person per line: <code>Full name, username, phone</code>. Username and phone are optional — we'll create a username from the name.</p>
      <textarea class="input" v-model="names" rows="8" placeholder="Nusrat Jahan&#10;Tanvir Ahmed, tanvir47&#10;Mitu Akter, , 01711000000" />
      <button class="btn accent block" :disabled="busy || !parsed.length">Create {{ parsed.length || '' }} account{{ parsed.length === 1 ? '' : 's' }}</button>
    </form>
  </Sheet>

  <Sheet :open="credentials.length > 0" @close="credentials = []">
    <div class="stack">
      <h2>Login details</h2>
      <div class="banner warn small">These passwords are shown only once. Share each privately — everyone will set their own password at first login.</div>
      <div v-for="c in credentials" :key="c.id" class="card flat stack" style="padding: .75rem">
        <b>{{ c.name }}</b>
        <div class="cred">Username: {{ c.username }}<br />Password: {{ c.password }}</div>
        <div class="row">
          <a class="btn sm grow" :href="whatsapp(c)" target="_blank" rel="noopener">Send on WhatsApp</a>
          <button class="btn sm ghost grow" @click="copy(credText(c))"><Icon name="copy" /> Copy</button>
        </div>
      </div>
      <button v-if="credentials.length > 1" class="btn ghost block" @click="copy(credentials.map(credText).join('\n\n'))">Copy all</button>
      <button class="btn block" @click="credentials = []">Done</button>
    </div>
  </Sheet>

  <Sheet :open="!!selected" @close="selected = null">
    <div v-if="selected" class="stack">
      <div class="row"><Avatar :user="selected" :size="48" /><div><h3 style="margin: 0">{{ selected.name }}</h3><div class="small muted">@{{ selected.username }}</div></div></div>
      <div class="list">
        <button class="list-item" @click="startChat(selected)"><Icon name="chat" style="width: 20px" /> Message</button>
        <button class="list-item" @click="reset(selected)"><Icon name="key" style="width: 20px" /> Reset password</button>
        <button class="list-item" @click="toggleActive(selected)"><Icon name="users" style="width: 20px" /> {{ selected.is_active ? 'Deactivate (frees a seat)' : 'Reactivate' }}</button>
        <button v-if="selected.is_active" class="list-item" @click="makeOwner(selected)"><Icon name="settings" style="width: 20px" /> Make group owner</button>
      </div>
    </div>
  </Sheet>
</template>
