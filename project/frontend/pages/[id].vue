<script setup lang="ts">
import 'highlight.js/styles/monokai.css';
import type { QAPair, Conversation, ChatResponse, ToolUsed } from '@/shared/types';

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
const streamedSteps = ref<{ name: string; result: Record<string, string> }[]>([])
const currentAnswer = ref<{ answer: string; tools_used: string[] } | null>(null)
const sendMessage = async (message: string) => {
    // setIsGenerating(true);
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

        // Check if response body exists
        if (!res.body) {
            throw new Error("No response body");
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();

        let done = false;
        let answer = { answer: "", tools_used: [] };
        let currentSteps: { name: string; result: Record<string, string> }[] = [];
        let buffer = "";
        let currentStepName = "";
        let currentStepContent = "";
        let insideStep = false;
        streamedSteps.value = []
        currentAnswer.value = null
        while (!done) {
            const { value, done: doneReading } = await reader.read();
            done = doneReading;

            if (value) {
                let chunkValue = decoder.decode(value, { stream: true });
                console.log(`Received chunk: ${chunkValue}`);
                buffer += chunkValue;

                // Process buffer for complete tokens
                while (buffer.length > 0) {
                    if (buffer.startsWith('<step><step_name>')) {
                        // Start of a new step
                        const stepNameEndIndex = buffer.indexOf('</step_name>');
                        if (stepNameEndIndex !== -1) {
                            const stepNameStart = buffer.indexOf('<step_name>') + '<step_name>'.length;
                            currentStepName = buffer.substring(stepNameStart, stepNameEndIndex);
                            console.log(`Starting step: ${currentStepName}`);

                            // Remove the processed part from buffer
                            buffer = buffer.substring(stepNameEndIndex + '</step_name>'.length);
                            insideStep = true;
                            currentStepContent = "";
                        } else {
                            // Wait for more data
                            break;
                        }
                    } else if (buffer.startsWith('</step>') && insideStep) {
                        // End of current step
                        buffer = buffer.substring('</step>'.length);
                        console.log(`Ending step: ${currentStepName}`);
                        console.log(`Step content: ${currentStepContent}`);
                        try {
                            // Extract only the first valid JSON object
                            const jsonMatch = currentStepContent.match(/^\s*(\{[\s\S]*?\})/);
                            if (!jsonMatch) throw new Error("No valid JSON found in step content");

                            const parsed = JSON.parse(jsonMatch[1]);

                            if (currentStepName === "final_answer") {
                                currentAnswer.value = parsed;
                                console.log(`✅ Final answer parsed: ${JSON.stringify(parsed)}`);
                            } else {
                                const newStep = {
                                    name: currentStepName,
                                    result: parsed
                                };
                                streamedSteps.value.push(newStep);
                                console.log(`✅ Step pushed: ${JSON.stringify(newStep)}`);
                            }
                        } catch (parseError) {
                            console.error(`❌ Error parsing step content for "${currentStepName}":`, parseError);
                            console.error(`Content was: ${currentStepContent}`);
                        }
                        insideStep = false;
                        currentStepName = "";
                        currentStepContent = "";
                        buffer = buffer.substring('</step>'.length);
                    } else if (insideStep) {
                        // We're inside a step, accumulate content
                        currentStepContent += buffer;
                        buffer = "";
                    } else {
                        // Look for the start of next step or consume one character
                        const nextStepIndex = buffer.indexOf('<step>');
                        if (nextStepIndex === -1) {
                            // No more steps in buffer, consume all
                            if (insideStep) {
                                currentStepContent += buffer;
                            }
                            buffer = "";
                        } else {
                            // Found next step, consume up to that point
                            if (insideStep) {
                                currentStepContent += buffer.substring(0, nextStepIndex);
                            }
                            buffer = buffer.substring(nextStepIndex);
                        }
                    }
                }

                // Update output with current progress
            }
        }

        console.log("Streaming completed");
        console.log(`Final steps: ${JSON.stringify(currentSteps)}`);
        console.log(`Final answer: ${JSON.stringify(answer)}`);
        if (currentAnswer.value) {
            // Build full tool_used objects from streamedSteps
            const toolUsages: ToolUsed[] = [];

            for (const step of streamedSteps.value) {
                if (currentAnswer.value.tools_used.includes(step.name)) {
                    toolUsages.push({
                        name: step.name,
                        args: step.result, // assuming `args` == `result` for now
                        output: JSON.stringify(step.result) // or a string summary
                    });
                }
            }

            conversation.value?.messages.push({
                question: message,
                response: {
                    answer: currentAnswer.value.answer,
                    tools_used: toolUsages,
                    steps: [...streamedSteps.value]
                }
            });
        }
    } catch (error) {
        console.error("Error in sendMessage:", error);
    } finally {
    }
};
</script>


<template>
    <div class="container pt-4 pb-0 h-full flex flex-col">
        <div class="flex-1 overflow-y-auto scroll pb-20"
            :class="conversation?.messages.length === 0 ? 'flex items-center justify-center' : ''">
            <div class="space-y-4 pt-10">
                <div v-if="loading" class="text-center">Loading conversation...</div>

                <div v-else-if="conversation">
                    <Output v-for="(qaPair, index) in conversation.messages" :key="index" :output="qaPair" />
                </div>

                <div v-if="streamedSteps.length" class="mt-10">
                    <h3 class="text-lg font-bold">Streaming Steps</h3>
                    <ul class="pl-4 space-y-1">
                        <li v-for="(step, index) in streamedSteps" :key="index">
                            <strong>{{ step.name }}</strong>: {{ step.result }}
                        </li>
                    </ul>
                </div>

                <div v-if="currentAnswer" class="mt-5">
                    <h3 class="text-lg font-bold">Final Answer</h3>
                    <p>{{ currentAnswer.answer }}</p>
                </div>

                <div v-else class="text-center text-red-500 mt-10" v-if="!loading && !conversation">
                    Failed to load conversation
                </div>
            </div>
        </div>

        <!-- Input fixed at the bottom -->
        <div
            class="sticky bottom-10    py-5 ">
            <TextInput @send_message="sendMessage" :conversation="conversation" />
        </div>
    </div>
</template>

<style scoped>
.scroll::-webkit-scrollbar {
    display: none;
}
</style>