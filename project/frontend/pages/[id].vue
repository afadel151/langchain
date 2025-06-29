<script setup lang="ts">
import 'highlight.js/styles/monokai.css';
import type { QAPair, Conversation, ChatResponse } from '@/shared/types';

const conversation = ref<Conversation | null>(null);
const loading = ref(true);
const conversationId = useRoute().params.id as string;

import { ref } from 'vue';

import TextInput from '../components/TextInput.vue';
onMounted(async () => {
    try {
        const response = await fetch(`http://127.0.0.1:8000/get_conversation?conversation_id=${conversationId}`);
        const data = await response.json();

        if (data.error) {
            console.error('Error loading conversation:', data.error);
        } else {
            conversation.value = data;
        }
    } catch (error) {
        console.error('Failed to load conversation:', error);
    } finally {
        loading.value = false;
    }
});
function update_outputs(output : QAPair){
    console.log(output);
    conversation.value?.messages.push(output)
    
}
</script>


<template>
    <div class="container pt-10 pb-32 h-full" :class="conversation?.messages.length === 0 ? 'flex items-center justify-center' : ''">
        <div class="flex flex-col-reverse w-full ">
            
            <TextInput @update-outputs="update_outputs"  :conversation="conversation" />
            <div v-if="loading" class="text-center">Loading conversation...</div>
            <div v-else-if="conversation" class="space-y-4">
                <Output v-for="(qaPair, index) in conversation.messages" :key="index" :output="qaPair" />
            </div>

            <div v-else class="text-center text-red-500">
                Failed to load conversation
            </div>
        </div>
    </div>
</template>