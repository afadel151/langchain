<script setup lang="ts">
import 'highlight.js/styles/monokai.css';
import { ref } from 'vue';
import type { ChatOutput } from '../shared/types';
import type { Conversation, ToolUsed } from '@/shared/types';
const isStreaming = ref(false);
const conversation = ref<Conversation | null>(null);
import TextInput from '../components/TextInput.vue';
const streamedSteps = ref<{ name: string; result: Record<string, string> }[]>([]);
const currentAnswer = ref<{ answer: string; tools_used: string[] } | null>(null);
const conversationId = ref('')

const updateCurrentMessage = (newAnswer: string, newToolsUsed: any[] = [], newSteps: any[] = []) => {
    if (conversation.value && conversation.value.messages.length > 0) {
        const lastMessageIndex = conversation.value.messages.length - 1;
        const lastMessage = conversation.value.messages[lastMessageIndex];
        conversation.value.messages[lastMessageIndex] = {
            ...lastMessage,
            response: {
                ...lastMessage.response,
                answer: newAnswer,
                tools_used: newToolsUsed.length > 0 ? newToolsUsed : lastMessage.response.tools_used,
                steps: newSteps.length > 0 ? newSteps : lastMessage.response.steps
            }
        };
    }
};

const addStepToCurrentMessage = (newStep: any) => {
    if (conversation.value && conversation.value.messages.length > 0) {
        const lastMessageIndex = conversation.value.messages.length - 1;
        const lastMessage = conversation.value.messages[lastMessageIndex];
        conversation.value.messages[lastMessageIndex] = {
            ...lastMessage,
            response: {
                ...lastMessage.response,
                steps: [...lastMessage.response.steps, newStep]
            }
        };
        console.log(conversation.value.messages[lastMessageIndex].response.steps);
    }
};

const sendMessage = async (message: string) => {
    try {
        const response = await fetch(`http://127.0.0.1:8000/create_title`, {
            method: 'POST',
            body: JSON.stringify({content : message })
        })
        console.log(response);
        conversationId.value = await response.json()
    } catch (error) {
        console.log(error);

    }
    isStreaming.value = true;
    if (conversation.value) {
        conversation.value.messages.push({
            question: message,
            response: {
                answer: "Thinking...",
                tools_used: [],
                steps: []
            }
        });
        console.log("Message added to conversation:", conversation.value.messages[conversation.value.messages.length - 1]);
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
                                const toolsUsedNames = parsed.tools_used || [];
                                const toolsUsedFormatted = streamedSteps.value
                                    .filter(step => toolsUsedNames.includes(step.name))
                                    .map(step => ({
                                        name: step.name,
                                        args: { ...step.result },
                                        output: step.result.output || JSON.stringify(step.result)
                                    }));
                                updateCurrentMessage(parsed.answer, toolsUsedFormatted);
                                console.log(`🎯 Updated message with new answer: "${parsed.answer}"`);
                            } else {
                                const newStep = {
                                    name: currentStepName,
                                    result: parsed
                                };
                                streamedSteps.value.push(newStep);
                                addStepToCurrentMessage(newStep);
                                console.log(`📝 Added step to message:`, newStep);
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
        console.log("💬 Final currentMessage:", conversation.value?.messages[conversation.value.messages.length - 1]);
        if (conversation.value?.messages[conversation.value.messages.length - 1] && currentAnswer.value) {
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
            const currentMessage = conversation.value.messages[conversation.value.messages.length - 1];
            if (!currentMessage.response.steps.some(step => step.name === "final_answer")) {
                addStepToCurrentMessage(finalAnswerStep);
            }
        }
    } catch (error) {
        console.error("❌ Error in sendMessage:", error);
    } finally {
        console.log("🔚 sendMessage finally block executed");

        isStreaming.value = false;
    }
};
</script>


<template>
    <div class="container flex pb-10 flex-col justify-center  pt-10   h-full">

        <div v-if="conversation != null" ref="scrollContainer" class="flex-1  overflow-y-auto scroll pb-20"
            :class="conversation?.messages.length === 0 ? 'flex items-center justify-center' : ''">
            <div class="space-y-4 pt-10">

                <Output v-for="(qaPair, index) in conversation?.messages" :key="index" :output="qaPair" />

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
            </div>
        </div>
        <p v-if="conversation == null" class="text-center text-5xl mb-10">What do you want to know</p>
        <div class="sticky bottom-0 py-5">
            <TextInput @send_message="sendMessage" :conversation="conversation" :disabled="isStreaming" />
        </div>
    </div>
</template>