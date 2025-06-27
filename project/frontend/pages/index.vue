<script setup lang="ts">
import 'highlight.js/styles/monokai.css';
import { ref } from 'vue';
import type { ChatOutput } from '../shared/types';
const outputs = ref<ChatOutput[]>([])
import TextInput from '../components/TextInput.vue';
function update_ouputs(newValue: ChatOutput[] | ((prev: ChatOutput[]) => ChatOutput[])) {
    if (typeof newValue === "function") {
        outputs.value = newValue(outputs.value);
    } else {
        outputs.value = newValue;
    }
}
</script>


<template>
    <div class="container pt-10 pb-32 h-full"
        :class="outputs.length === 0 ? 'flex items-center justify-center' : ''">
        <div class="w-full ">
            <h1 v-if="outputs.length === 0" class="text-4xl text-center mb-10">What do you want to know</h1>
            <TextInput @update-outputs="update_ouputs" :outputs="outputs" />
            <Output v-for="(output,i) in outputs" :output="output" :key="i" />
        </div>
    </div>
</template>