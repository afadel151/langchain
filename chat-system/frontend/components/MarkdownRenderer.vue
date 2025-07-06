<template>
  <div>
    <Markdown :source="source" />
  </div>
</template>

<script setup>
defineProps({
  source: {
    type: String,
    default: '# Hello World! **he**'
  }
})
import Markdown from 'vue3-markdown-it'
</script>