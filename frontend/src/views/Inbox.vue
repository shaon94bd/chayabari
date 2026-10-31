<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import { usePoll } from '@/composables/usePoll'
import { timeAgo } from '@/utils'
import Avatar from '@/components/Avatar.vue'
import Empty from '@/components/Empty.vue'

const convs = ref([])
const loading = ref(true)
const load = async () => { convs.value = await api.get('/conversations/'); loading.value = false }
onMounted(load)
usePoll(load, 10000)
</script>

<template>
  <div class="page">
    <h1>Chat</h1>
    <div v-if="loading" class="spinner" />
    <div v-else-if="convs.length" class="list">
      <RouterLink v-for="c in convs" :key="c.id" :to="`/chat/${c.id}`" class="list-item">
        <div v-if="c.kind === 'group'" class="avatar" style="width: 46px; height: 46px; background: var(--ink); color: #fff">👥</div>
        <Avatar v-else :user="c.other" :size="46" />
        <div class="grow">
          <div class="row between">
            <b class="ellipsis">{{ c.title }}</b>
            <span class="tiny faint" v-if="c.last_message">{{ timeAgo(c.last_message.created_at) }}</span>
          </div>
          <div class="row between">
            <span class="small muted ellipsis">
              <template v-if="c.last_message">{{ c.kind === 'group' ? c.last_message.sender + ': ' : '' }}{{ c.last_message.body }}</template>
              <template v-else>No messages yet</template>
            </span>
            <span v-if="c.unread" class="badge accent">{{ c.unread }}</span>
          </div>
        </div>
      </RouterLink>
    </div>
    <Empty v-else icon="💬" title="No conversations" text="Message an artist from any artwork page." />
  </div>
</template>
