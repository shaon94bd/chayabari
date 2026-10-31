<script setup>
import { computed } from 'vue'
const props = defineProps({ user: Object, size: { type: Number, default: 40 } })
const initials = computed(() =>
  (props.user?.name || props.user?.username || '?').split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase(),
)
</script>

<template>
  <div class="avatar" :style="{ width: size + 'px', height: size + 'px', fontSize: size * 0.38 + 'px' }">
    <img v-if="user?.avatar" :src="user.avatar" alt="" />
    <span v-else>{{ initials }}</span>
  </div>
</template>
