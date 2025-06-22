<script setup lang="ts">
import 'highlight.js/styles/monokai.css';
import type { ChatOutput } from '~/shared/types';
const text = `# Hello World! **she**`
const outputs = ref<ChatOutput[]>([])


</script>


<template>
    <div class="container pt-10 pb-32 min-h-screen"
        :class="outputs.length === 0 ? 'flex items-center justify-center' : ''">
    >
        <div class="w-full">
            <h1 v-if="outputs.length === 0">What do you want to know</h1>
        </div>
    </div>
</template>