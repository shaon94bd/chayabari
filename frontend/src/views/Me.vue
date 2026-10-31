<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '@/stores/auth'
import { dateShort } from '@/utils'
import Avatar from '@/components/Avatar.vue'
import Icon from '@/components/Icon.vue'
import InactiveBanner from '@/components/InactiveBanner.vue'

const auth = useAuth()
const router = useRouter()
const logout = () => { auth.logout(); router.replace('/') }
</script>

<template>
  <div class="page stack">
    <div class="row">
      <Avatar :user="auth.user" :size="64" />
      <div class="grow">
        <h2 style="margin: 0">{{ auth.user.name }}</h2>
        <div class="small muted">@{{ auth.user.username }} · {{ { owner: 'Batch owner', member: 'Artist', collector: 'Collector' }[auth.user.role] }}</div>
      </div>
    </div>
    <InactiveBanner />

    <div v-if="auth.batch" class="card">
      <div class="row between">
        <div>
          <b>{{ auth.batch.name }}</b>
          <div class="small muted">{{ auth.batch.institution }}<span v-if="auth.batch.session"> · {{ auth.batch.session }}</span></div>
        </div>
        <span class="badge" :class="auth.batch.is_active ? 'ok' : 'warn'">
          {{ auth.batch.subscription_status === 'trial' ? 'Trial' : auth.batch.is_active ? 'Active' : 'Expired' }}
        </span>
      </div>
      <div v-if="auth.batch.subscription_ends_at" class="tiny faint" style="margin-top: .3rem">
        {{ auth.batch.is_active ? 'Until' : 'Ended' }} {{ dateShort(auth.batch.subscription_ends_at) }}
      </div>
    </div>

    <div class="list">
      <RouterLink v-if="auth.isStudent" :to="`/artists/${auth.user.username}`" class="list-item"><Icon name="frame" style="width: 22px" /><span class="grow">My portfolio</span><span class="chev">›</span></RouterLink>
      <RouterLink to="/orders" class="list-item"><Icon name="bag" style="width: 22px" /><span class="grow">{{ auth.isStudent ? 'Sales & purchases' : 'My purchases' }}</span><span class="chev">›</span></RouterLink>
      <RouterLink to="/me/edit" class="list-item"><Icon name="edit" style="width: 22px" /><span class="grow">Edit profile</span><span class="chev">›</span></RouterLink>
      <RouterLink to="/change-password" class="list-item"><Icon name="key" style="width: 22px" /><span class="grow">Change password</span><span class="chev">›</span></RouterLink>
    </div>

    <div v-if="auth.isStudent" class="list">
      <RouterLink :to="`/b/${auth.batch.slug}`" class="list-item"><Icon name="globe" style="width: 22px" /><span class="grow">Public batch page</span><span class="chev">›</span></RouterLink>
      <RouterLink to="/batch/members" class="list-item"><Icon name="users" style="width: 22px" /><span class="grow">{{ auth.isOwner ? 'Manage members' : 'Batch members' }}</span><span class="chev">›</span></RouterLink>
      <RouterLink to="/batch/billing" class="list-item"><Icon name="card" style="width: 22px" /><span class="grow">Subscription</span><span class="chev">›</span></RouterLink>
      <RouterLink v-if="auth.isOwner" to="/batch/settings" class="list-item"><Icon name="settings" style="width: 22px" /><span class="grow">Batch settings</span><span class="chev">›</span></RouterLink>
    </div>

    <button class="btn ghost block" @click="logout"><Icon name="logout" /> Log out</button>
  </div>
</template>
