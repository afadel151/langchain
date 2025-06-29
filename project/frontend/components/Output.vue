<script setup lang="ts">
import type { QAPair } from "~/shared/types";
const props = defineProps<{
    output: QAPair; 
}>();
const detailsHidden = !!props.output.response?.answer;
import Steps from "./Steps.vue";
import MarkdownRenderer from "./MarkdownRenderer.vue";
</script>

<template>
    <div className="border-t mt-10  border-gray-700 py-10 first-of-type:pt-0 first-of-type:border-t-0">
        <p class="max-w-[75%] w-fit  ml-auto bg-gray-200 text-gray-900 text-base rounded-2xl rounded-tr-sm px-4 py-2 mb-2">
            {{ output.question }}
        </p>
        <Steps v-if="output.response.steps && output.response.steps.length > 0" :steps="output.response.steps"
            :done="false" />

        <div class="mt-5 prose dark:prose-invert min-w-full prose-pre:whitespace-pre-wrap">
            <MarkdownRenderer :source="output.response?.answer" />
        </div>
        <div v-if="output.response?.tools_used?.length > 0" class="flex items-baseline mt-5 gap-1">
            <p class="text-xs text-gray-500">Tools used:</p>
            <div class="flex flex-wrap items-center gap-1">
                <p v-for="(tool, i) in output.response.tools_used" :key="i"
                    class="text-xs px-1 py-[1px] bg-gray-800 rounded text-white">
                    {{ tool.name }}
                </p>
            </div>
        </div>
    </div>
</template>