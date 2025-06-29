<script setup lang="ts">
import 'highlight.js/styles/monokai.css';
import type { Conversation, ToolUsed } from '@/shared/types';

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


const streamedSteps = ref<{ name: string; result: Record<string, string> }[]>([]);
const currentAnswer = ref<{ answer: string; tools_used: string[] } | null>(null);


const isStreaming = ref(false);

import { watch, nextTick } from 'vue'

const scrollContainer : any = ref(null)

watch(
    () => conversation.value?.messages.length,
    async () => {
        await nextTick()
        if (scrollContainer.value) {
            scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
        }
    }
)
const currentMessage = ref<{
    question: string;
    response: {
        answer: string;
        tools_used: ToolUsed[];
        steps: { name: string; result: Record<string, any> }[];
    };
} | null>(null);

const sendMessage = async (message: string) => {
    isStreaming.value = true;
    currentMessage.value = {
        question: message,
        response: {
            answer: "Thinking...",
            tools_used: [],
            steps: []
        }
    };
    if (conversation.value) {
        conversation.value.messages.push(currentMessage.value);
        console.log("Message added to conversation:", currentMessage.value);
    }
    try {
        const res = await fetch(`http://127.0.0.1:8000/invoke`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ content: message, conversation_id: conversationId })
        });
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        if (!res.body) {
            throw new Error("No response body");
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let done = false;
        let buffer = "";
        let currentStepName = "";
        let currentStepContent = "";
        let insideStep = false;
        streamedSteps.value = [];
        currentAnswer.value = null;
        while (!done) {
            try {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;
                if (value) {
                    let chunkValue = decoder.decode(value, { stream: true });
                    console.log(`📦 Received chunk: "${chunkValue}"`);
                    buffer += chunkValue;
                }
                while (buffer.length > 0) {
                    if (buffer.startsWith('<step><step_name>')) {
                        const stepNameEndIndex = buffer.indexOf('</step_name>');
                        if (stepNameEndIndex !== -1) {
                            const stepNameStart = buffer.indexOf('<step_name>') + '<step_name>'.length;
                            currentStepName = buffer.substring(stepNameStart, stepNameEndIndex);
                            console.log(`Starting step: ${currentStepName}`);
                            buffer = buffer.substring(stepNameEndIndex + '</step_name>'.length);
                            insideStep = true;
                            currentStepContent = "";
                        } else {
                            break;
                        }
                    } else if (buffer.startsWith('</step>') && insideStep) {
                        buffer = buffer.substring('</step>'.length);
                        console.log(`Ending step: ${currentStepName}`);
                        console.log(`Step content: ${currentStepContent}`);
                        try {
                            const jsonMatch = currentStepContent.match(/^\s*(\{[\s\S]*?\})/);
                            if (!jsonMatch) throw new Error("No valid JSON found in step content");
                            const parsed = JSON.parse(jsonMatch[1])
                            if (currentStepName === "final_answer") {
                                currentAnswer.value = parsed;
                                console.log(`✅ Final answer parsed: ${JSON.stringify(parsed)}`);
                                if (currentMessage.value) {
                                    currentMessage.value.response.answer = parsed.answer;
                                    console.log(`🎯 Updated message answer: "${parsed.answer}"`);
                                    const toolsUsedNames = parsed.tools_used || [];
                                    currentMessage.value.response.tools_used = streamedSteps.value
                                        .filter(step => toolsUsedNames.includes(step.name))
                                        .map(step => ({
                                            name: step.name,
                                            args: { ...step.result },
                                            output: step.result.output || JSON.stringify(step.result)
                                        }));

                                    console.log(`🔧 Updated tools_used:`, currentMessage.value.response.tools_used);
                                }
                            } else {
                                const newStep = {
                                    name: currentStepName,
                                    result: parsed
                                };
                                streamedSteps.value.push(newStep);
                                if (currentMessage.value) {
                                    currentMessage.value.response.steps.push(newStep);
                                    console.log(`📝 Added step to message:`, newStep);
                                }

                                console.log(`✅ Step pushed: ${JSON.stringify(newStep)}`);
                            }
                        } catch (parseError) {
                            console.error(`❌ Error parsing step content for "${currentStepName}":`, parseError);
                            console.error(`Content was: ${currentStepContent}`);
                        }

                        insideStep = false;
                        currentStepName = "";
                        currentStepContent = "";
                    } else if (insideStep) {
                        currentStepContent += buffer;
                        buffer = "";
                    } else {
                        const nextStepIndex = buffer.indexOf('<step>');
                        if (nextStepIndex === -1) {
                            if (insideStep) {
                                currentStepContent += buffer;
                            }
                            buffer = "";
                        } else {
                            if (insideStep) {
                                currentStepContent += buffer.substring(0, nextStepIndex);
                            }
                            buffer = buffer.substring(nextStepIndex);
                        }
                    }
                }
            } catch (readError) {
                console.error("❌ Stream read error:", readError);
                break;
            }
        }
        console.log("🏁 Streaming completed");
        console.log("📊 Final streamedSteps:", streamedSteps.value);
        console.log("📋 Final currentAnswer:", currentAnswer.value);
        console.log("💬 Final currentMessage:", currentMessage.value);
        if (currentMessage.value && currentAnswer.value) {
            const finalAnswerStep = {
                name: "final_answer",
                result: {
                    tools_used: currentAnswer.value.tools_used,
                    answer: currentAnswer.value.answer,
                    output: JSON.stringify({
                        answer: currentAnswer.value.answer,
                        tools_used: currentAnswer.value.tools_used
                    })
                }
            };
            if (!currentMessage.value.response.steps.some(step => step.name === "final_answer")) {
                currentMessage.value.response.steps.push(finalAnswerStep);
            }
        }
    } catch (error) {
        console.error("❌ Error in sendMessage:", error);
        if (currentMessage.value) {
            currentMessage.value.response.answer = "Error occurred while processing your request.";
        }
    } finally {
        console.log("🔚 sendMessage finally block executed");
        isStreaming.value = false;
        currentMessage.value = null;
    }
};
</script>

<template>
    <div class="container pt-4 pb-0 h-full flex flex-col">
        <div ref="scrollContainer" class="flex-1 overflow-y-auto scroll pb-20"
            :class="conversation?.messages.length === 0 ? 'flex items-center justify-center' : ''">
            <div class="space-y-4 pt-10">
                <div v-if="loading" class="text-center">Loading conversation...</div>
                <div v-else-if="conversation">
                    <div class="mb-4 p-2 bg-green-100 rounded text-sm">
                        Debug: Total messages: {{ conversation.messages.length }}
                        <br>Is streaming: {{ isStreaming }}
                    </div>
                    <Output v-for="(qaPair, index) in conversation.messages" :key="index"
                        :output="qaPair" />
                </div>
                <div v-if="isStreaming && streamedSteps.length" class="mt-10 p-4 bg-gray-100 rounded">
                    <h3 class="text-lg font-bold">Debug: Streaming Steps</h3>
                    <ul class="pl-4 space-y-1">
                        <li v-for="(step, index) in streamedSteps" :key="index">
                            <strong>{{ step.name }}</strong>: {{ JSON.stringify(step.result) }}
                        </li>
                    </ul>
                </div>
                <div v-if="isStreaming && currentAnswer" class="mt-5 p-4 bg-blue-100 rounded">
                    <h3 class="text-lg font-bold">Debug: Current Answer</h3>
                    <p>{{ currentAnswer.answer }}</p>
                    <p><strong>Tools used:</strong> {{ currentAnswer.tools_used.join(', ') }}</p>
                </div>
                <div v-else class="text-center text-red-500 mt-10" v-if="!loading && !conversation">
                    Failed to load conversation
                </div>
            </div>
        </div>
        <div class="sticky bottom-10 py-5">
            <TextInput @send_message="sendMessage" :conversation="conversation" :disabled="isStreaming" />
        </div>
    </div>
</template>

<style scoped>
.scroll::-webkit-scrollbar {
    display: none;
}
</style>