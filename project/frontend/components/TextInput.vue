<script setup lang="ts">
import type { ChatOutput } from '@/shared/types'
import { IncompleteJsonParser } from 'incomplete-json-parser';

const parser = new IncompleteJsonParser();
const isGenerating = ref(false)
const text = ref('')
const textAreaRef = ref<HTMLTextAreaElement | null>(null)
function setOutputs(newValue: ChatOutput[] | ((prev: ChatOutput[]) => ChatOutput[])) {
    if (typeof newValue === 'function') {
        outputs.value = newValue(outputs.value)
    } else {
        outputs.value = newValue
    }
}
const setIsGenerating = (state: boolean) => {
}

const outputs = ref<ChatOutput[]>([])

async function subimt(e: Event) {
    e.preventDefault()

    text.value = ""
}

const sendMessage = async (message: string) => {
    const newOutputs = [...outputs.value, {
        question: text.value,
        steps: [],
        result: {
            answer: '',
            tools_used: [],
        }
    }]
    setOutputs(newOutputs)
    setIsGenerating(true);
    try {
        const res = await fetch(`http://localhost:8000/invoke?content=${text}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(text),
        });

        if (!res.ok) {
            throw new Error("Error");
        }

        const data = res.body;
        if (!data) {
            setIsGenerating(false);
            return;
        }

        const reader = data.getReader();
        const decoder = new TextDecoder();
        let done = false;
        let answer = { answer: "", tools_used: [] };
        let currentSteps: { name: string; result: Record<string, string> }[] = [];
        let buffer = "";
        while (!done) {
            const { value, done: doneReading } = await reader.read();
            done = doneReading;
            let chunkValue = decoder.decode(value);
            console.log(`chunk : ${chunkValue}`);
            buffer += chunkValue;
            if (buffer.includes("</step_name>")) {
                const stepNameMatch = buffer.match(/<step_name>([^<]*)<\/step_name>/);
                if (stepNameMatch) {
                    const [_, stepName] = stepNameMatch;
                    try {
                        if (stepName !== "final_answer") {
                            const fullStepPattern =
                                /<step><step_name>([^<]*)<\/step_name>([^<]*?)(?=<step>|<\/step>|$)/g;
                            const matches = [...buffer.matchAll(fullStepPattern)];
                            for (const match of matches) {
                                const [fullMatch, matchStepName, jsonStr] = match;
                                if (jsonStr) {
                                    try {
                                        const result = JSON.parse(jsonStr);
                                        currentSteps.push({ name: matchStepName, result });
                                        buffer = buffer.replace(fullMatch, "");
                                    } catch (error) {
                                    }
                                }
                            }
                        } else {
                            // If it's the final answer step, parse the streaming JSON using incomplete-json-parser
                            const jsonMatch = buffer.match(
                                /(?<=<step><step_name>final_answer<\/step_name>)(.*)/
                            );
                            if (jsonMatch) {
                                const [_, jsonStr] = jsonMatch;
                                parser.write(jsonStr);
                                const result = parser.getObjects();
                                answer = result;
                                parser.reset();
                            }
                        }
                    } catch (error) {
                        console.error("Error parsing step name:", error);
                    }
                }
            }
            // Update output with current content and steps
            setOutputs((prevOuputs) => {
                const lastOutput = prevOuputs[prevOuputs.length - 1];
                return [
                    ...prevOuputs.slice(0, -1),
                    {
                        ...lastOutput,
                        steps: currentSteps,
                        result: answer,
                    },
                ];
            });
        }
    }
    catch (error) {
        console.error("Error:", error);
        setIsGenerating(false);
    }
    finally {
        setIsGenerating(false);
    }
};

function submitOnEnter(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        subimt(event);
    }
}
const adjustHeight = () => {
    nextTick(() => {
        const textArea = textAreaRef.value
        if (textArea) {
            textArea.style.height = 'auto'
            textArea.style.height = `${textArea.scrollHeight}px`
        }
    })
}

watch(text, (newValue) => {
    if (textAreaRef.value) {
        adjustHeight();
    }
});
function handleResize() {
    adjustHeight()
}

// When component is mounted
onMounted(() => {
    window.addEventListener('resize', handleResize)
    adjustHeight() // Optionally call once on mount
})

// Clean up when component is destroyed
onBeforeUnmount(() => {
    window.removeEventListener('resize', handleResize)
})
import { ArrowRight } from 'lucide-vue-next';
</script>

<template>
    <form :onsubmit="subimt" class="flex gap-3 z-10"
        :class="outputs.length > 0 ? 'fixed bottom-0 left-0 right-0 bg-white p-4 shadow-lg' : ''">
        <div class="w-full flex items-center bg-gray-800 rounded border border-gray-600">
            <Textarea v-model="text" ref="textAreaRef" @keydown.enter.prevent="submitOnEnter" @input="adjustHeight"
                class="w-full p-2 bg-transparent text-white resize-none border-0 focus:outline-none"
                placeholder="Type your message here..." />
            <Button type="submit" :disabled="isGenerating || !text" class="rounded-full">
                <ArrowRight />
            </Button>

        </div>
    </form>
</template>