<script setup>
import { ref, watch } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({ modelValue: [File, null], current: String, label: { type: String, default: 'Add photo' }, ratio: { type: String, default: '4/5' } })
const emit = defineEmits(['update:modelValue'])
const preview = ref(props.current || null)
watch(() => props.current, (v) => { if (!props.modelValue) preview.value = v })
function pick(e) {
  const f = e.target.files?.[0]
  if (!f) return
  emit('update:modelValue', f)
  preview.value = URL.createObjectURL(f)
}
</script>

<template>
  <label class="picker" :style="{ aspectRatio: ratio }">
    <img v-if="preview" :src="preview" alt="" />
    <div v-else class="picker-empty"><Icon name="image" /><span>{{ label }}</span></div>
    <input type="file" accept="image/*" @change="pick" hidden />
  </label>
</template>

<style scoped>
.picker { display: block; width: 100%; max-height: 60vh; border-radius: var(--radius); overflow: hidden; background: var(--card); border: 2px dashed var(--line); cursor: pointer; }
.picker img { width: 100%; height: 100%; object-fit: contain; background: #eee7dd; }
.picker-empty { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: .4rem; color: var(--ink-2); font-weight: 500; }
.picker-empty svg { width: 36px; height: 36px; }
</style>
