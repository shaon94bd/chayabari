<script setup>
defineProps({ open: Boolean })
const emit = defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="sheet-backdrop" @click.self="emit('close')">
      <div class="sheet" role="dialog">
        <div class="grabber" />
        <slot />
      </div>
    </div>
  </Teleport>
</template>
